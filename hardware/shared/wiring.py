"""Tool-independent board coordinates, nets, buses, and host pin assignments.

Schematic and PCB implementations consume this contract instead of owning
parallel naming and mapping decisions.
"""

from __future__ import annotations

from dataclasses import dataclass

from .dimensions import GRID_COUNT, HALL_BANKS
from .hall_banks import HallBank, SquarePosition

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


@dataclass(frozen=True, slots=True)
class ExpanderChannel:
    """The GPIO-expander bank and P0–P7 channel assigned to a square."""

    bank: HallBank
    pin_index: int


def parse_square(name: str) -> SquarePosition:
    return SquarePosition.parse(name)


def sense_net(square_name: str) -> str:
    return f"SQ_{square_name}"


def button_net(name: str) -> str:
    return f"BTN_{name}"


def expander_of(position: SquarePosition) -> ExpanderChannel:
    """Bank and P0–P7 channel owning this square."""
    for bank in HALL_BANKS:
        for pin_index, member in enumerate(bank.members):
            if member == position:
                return ExpanderChannel(bank, pin_index)
    raise ValueError(
        f"invalid square coordinates {(position.file_index, position.rank)}"
    )


def led_chain_order() -> list[SquarePosition]:
    """Squares in chain order: a serpentine by rank starting at A1."""
    chain: list[SquarePosition] = []
    for index in range(GRID_COUNT**2):
        rank = index // GRID_COUNT
        offset = index % GRID_COUNT
        file_index = offset if rank % 2 == 0 else GRID_COUNT - 1 - offset
        chain.append(SquarePosition(file_index, rank))
    return chain
