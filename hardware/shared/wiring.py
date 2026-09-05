"""Tool-independent board coordinates, nets, buses, and host pin assignments.

Schematic and PCB implementations consume this contract instead of owning
parallel naming and mapping decisions.
"""

from __future__ import annotations

from .dimensions import GRID_COUNT, HALL_BANKS
from .hall_banks import FILES, square

GRID = 2.54

# --- I2C bus ----------------------------------------------------------------
# Eight compact Hall banks share the bus with the display. Acquisition is polled.
EXPANDER_COUNT = len(HALL_BANKS)
OLED_ADDRESS = 0x3C
SDA_NET = "I2C_SDA"
SCL_NET = "I2C_SCL"

# --- LED chain --------------------------------------------------------------
# The Pi drives 3.3 V SPI into a buffer; the chain itself runs at 5 V.
SPI_DATA_NET = "SPI_DATA_3V3"
SPI_CLOCK_NET = "SPI_CLK_3V3"
LED_DATA_NET = "LED_DATA_5V"
LED_CLOCK_NET = "LED_CLK_5V"
LED_DATA_END_NET = "LED_DATA_LAST"
LED_CLOCK_END_NET = "LED_CLK_LAST"

# --- Control panel ----------------------------------------------------------
# Twelve identical buttons straight onto Broadcom lines. Nothing here goes
# through an expander, so remapping a button is a host-software change only.
BUTTON_GPIO: dict[str, int] = {
    "UP": 5,
    "DOWN": 6,
    "LEFT": 12,
    "RIGHT": 13,
    "OK": 16,
    "RESET": 17,
    "PASS": 19,
    "F1": 20,
    "F2": 21,
    "F3": 22,
    "F4": 23,
    "F5": 24,
}
BUTTON_NAMES = tuple(BUTTON_GPIO)

# --- Pi line assignment -----------------------------------------------------
SDA_GPIO = 2
SCL_GPIO = 3
SPI_DATA_GPIO = 10
SPI_CLOCK_GPIO = 11
ASSIGNED_GPIO = (
    SDA_GPIO,
    SCL_GPIO,
    SPI_DATA_GPIO,
    SPI_CLOCK_GPIO,
    *BUTTON_GPIO.values(),
)


def parse_square(name: str) -> tuple[int, int]:
    text = name.strip().upper()
    if len(text) < 2 or text[0] not in FILES:
        raise ValueError(f"invalid square {name!r}")
    rank = int(text[1:]) - 1
    if rank not in range(GRID_COUNT):
        raise ValueError(f"invalid square {name!r}")
    return FILES.index(text[0]), rank


def sense_net(square_name: str) -> str:
    return f"SQ_{square_name}"


def button_net(name: str) -> str:
    return f"BTN_{name}"


def expander_address(index: int) -> int:
    return HALL_BANKS[index].address


def expander_straps(index: int) -> tuple[bool, bool, bool]:
    return HALL_BANKS[index].straps


def expander_of(file_index: int, rank: int) -> tuple[int, int]:
    """Bank and P0–P7 channel owning this square."""
    for bank in HALL_BANKS:
        if (file_index, rank) in bank.members:
            return bank.index, bank.members.index((file_index, rank))
    raise ValueError(f"invalid square coordinates {(file_index, rank)}")


def expander_squares(index: int) -> list[tuple[int, str]]:
    return [
        (pin, square(*member)) for pin, member in enumerate(HALL_BANKS[index].members)
    ]


def led_chain_order() -> list[tuple[str, int, int]]:
    """Squares in chain order: a serpentine by rank starting at A1."""
    chain: list[tuple[str, int, int]] = []
    for index in range(GRID_COUNT**2):
        rank = index // GRID_COUNT
        offset = index % GRID_COUNT
        file_index = offset if rank % 2 == 0 else GRID_COUNT - 1 - offset
        chain.append((square(file_index, rank), file_index, rank))
    return chain
