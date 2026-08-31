"""Tool-independent board coordinates, nets, buses, and host pin assignments.

Schematic and PCB implementations consume this contract instead of owning
parallel naming and mapping decisions.
"""

from __future__ import annotations

from .dimensions import GRID_COUNT

FILES = "ABCDEFGH"
GRID = 2.54

# --- I2C bus ----------------------------------------------------------------
# Four expanders, one per 4x4 quadrant, plus the display. A2 is always grounded
# and A1/A0 encode the quadrant index, so the addresses run consecutively.
EXPANDER_COUNT = 4
EXPANDER_BASE_ADDRESS = 0x20
OLED_ADDRESS = 0x3C
SDA_NET = "I2C_SDA"
SCL_NET = "I2C_SCL"
SENSE_IRQ_NET = "SENSE_IRQ"

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
SENSE_IRQ_GPIO = 4
SPI_DATA_GPIO = 10
SPI_CLOCK_GPIO = 11
ASSIGNED_GPIO = (
    SDA_GPIO,
    SCL_GPIO,
    SENSE_IRQ_GPIO,
    SPI_DATA_GPIO,
    SPI_CLOCK_GPIO,
    *BUTTON_GPIO.values(),
)


def square(file_index: int, rank: int) -> str:
    return f"{FILES[file_index]}{rank + 1}"


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
    return EXPANDER_BASE_ADDRESS + index


def expander_straps(index: int) -> tuple[bool, bool, bool]:
    """A0, A1, A2 strap levels. True means tied to 3.3 V."""
    return (bool(index & 1), bool(index & 2), False)


def expander_of(file_index: int, rank: int) -> tuple[int, int]:
    """Which expander reads a square, and which of its sixteen pins.

    Quadrants keep every reed trace short on a 320 mm board: an expander sits at
    the centre of the sixteen squares it serves. Pins 0-7 are port A, the lower
    two ranks of the quadrant, and 8-15 are port B, the upper two.
    """
    index = (rank // 4) * 2 + (file_index // 4)
    pin = (rank % 4) * 4 + (file_index % 4)
    return index, pin


def expander_quadrant(index: int) -> str:
    """The square range an expander covers, for labelling the sheet."""
    first_file = (index % 2) * 4
    first_rank = (index // 2) * 4
    return f"{square(first_file, first_rank)}-{square(first_file + 3, first_rank + 3)}"


def expander_squares(index: int) -> list[tuple[int, str]]:
    """Every square an expander reads, ordered by its own pin number."""
    found: list[tuple[int, str]] = []
    for rank in range(GRID_COUNT):
        for file_index in range(GRID_COUNT):
            owner, pin = expander_of(file_index, rank)
            if owner == index:
                found.append((pin, square(file_index, rank)))
    found.sort()
    return found


def led_chain_order() -> list[tuple[str, int, int]]:
    """Squares in chain order: a serpentine by rank starting at A1."""
    chain: list[tuple[str, int, int]] = []
    for index in range(GRID_COUNT**2):
        rank = index // GRID_COUNT
        offset = index % GRID_COUNT
        file_index = offset if rank % 2 == 0 else GRID_COUNT - 1 - offset
        chain.append((square(file_index, rank), file_index, rank))
    return chain
