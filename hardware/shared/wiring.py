"""Tool-independent board coordinates, nets, buses, and host pin assignments.

Schematic and PCB implementations consume this contract instead of owning
parallel naming and mapping decisions.

Role: the naming authority for electrical nets and the Pi GPIO assignments, plus the
square -> (Hall bank, expander channel) mapping. The PCB assemblies, schematic
generator and tests import these names; the firmware's hand-maintained pin
declarations (`apps/firmware/src/hardware/pins.rs`) must be kept in step with the GPIO
numbers here (there is no generator, so changing one side means changing both).
"""

from __future__ import annotations

from dataclasses import dataclass

from .dimensions import HALL_BANKS
from .hall_banks import HallBank, SquarePosition
from .panel_buttons import PANEL_BUTTONS

# --- I2C bus ----------------------------------------------------------------
# Eight compact Hall banks share the bus with the display. Acquisition is polled.
# One expander per bank, so the count follows the bank layout rather than a literal.
EXPANDER_COUNT = len(HALL_BANKS)
# 7-bit I2C address of the display; the expanders use 0x20+ (see HallBank.address),
# so the two ranges cannot collide.
OLED_ADDRESS = 0x3C
SDA_NET = "I2C_SDA"
SCL_NET = "I2C_SCL"

# --- LED chain --------------------------------------------------------------
# The Pi drives 3.3 V SPI into a buffer; the chain itself runs at 5 V.
# Net names carry their voltage domain (3V3 vs 5V) so a schematic reader can see
# where the level shift sits; the _3V3 pair is the Pi side, the _5V pair the LEDs.
SPI_DATA_NET = "SPI_DATA_3V3"
SPI_CLOCK_NET = "SPI_CLK_3V3"
LED_DATA_NET = "LED_DATA_5V"
# U5 output to R9 (S5 source termination); LED_DATA_5V runs on from R9.
LED_DATA_BUFFER_NET = "LED_DATA_BUF"
LED_CLOCK_NET = "LED_CLK_5V"
# S6 LED rail switch (user decision D1, interface H5): the LEDs run from LED_5V,
# switched from +5V by Q1 when the Pi drives LED_EN high; LED_EN_N (Q2 drain, 5 V
# logic, active low) gates Q1 and the buffer's output enables.
LED_SUPPLY_NET = "LED_5V"
LED_ENABLE_NET = "LED_EN"
LED_ENABLE_N_NET = "LED_EN_N"
# S6b (H6): U75 OR of Q1's gate and LED_EN_N, the buffer's 1OE/2OE (active low).
LED_OUTPUT_ENABLE_N_NET = "LED_OE_N"


def led_link_nets(left: SquarePosition, right: SquarePosition) -> tuple[str, str]:
    """Name the data and clock link by its two physical squares.

    Each LED-to-LED hop needs its own pair of nets because the chain is
    daisy-chained: one LED's output is a different net from the next LED's input.
    This is only the fallback for a hop not in `led_link_names.LEGACY_NAMES`
    (which `led_link_names.for_squares` consults first); currently every hop is
    in that table, so no board net uses these generated names yet.
    """
    link = f"{left.name}_TO_{right.name}"
    return (f"LED_DATA_{link}", f"LED_CLOCK_{link}")


# --- Pi line assignment -----------------------------------------------------
# BCM GPIO numbers. 2/3 are the Pi's I2C1 pins and 10/11 its SPI0 MOSI/SCLK, which
# is why these are fixed by the hardware peripherals rather than free choices.
# Button GPIOs come from panel_buttons.py so each is defined exactly once.
SDA_GPIO = 2
SCL_GPIO = 3
SPI_DATA_GPIO = 10
SPI_CLOCK_GPIO = 11
# LED rail enable (header pin 37): BCM2835 peripherals 6.2 reset pull Low, so the
# rail stays off while the Pi boots; firmware output, default low (S6 H5/F).
LED_EN_GPIO = 26
# Every GPIO the board uses; checked by hardware/pcb/tests/board/test_firmware_pins.py.
ASSIGNED_GPIO = (
    SDA_GPIO,
    SCL_GPIO,
    SPI_DATA_GPIO,
    SPI_CLOCK_GPIO,
    LED_EN_GPIO,
    *(button.gpio for button in PANEL_BUTTONS),
)


@dataclass(frozen=True, slots=True)
class ExpanderChannel:
    """The GPIO-expander bank and P0–P7 channel assigned to a square."""

    bank: HallBank
    pin_index: int


def parse_square(name: str) -> SquarePosition:
    """Convenience alias so net/mapping callers need not import hall_banks."""
    return SquarePosition.parse(name)


def sense_net(square_name: str) -> str:
    """Name of the net carrying one square's Hall output (e.g. SQ_E4).

    The same string is used by the schematic, routing and tests, so renaming it
    here renames the net everywhere.
    """
    return f"SQ_{square_name}"


def expander_of(position: SquarePosition) -> ExpanderChannel:
    """Bank and P0–P7 channel owning this square.

    Linear search is fine: 8 banks x 8 members, run only at build time.
    """
    for bank in HALL_BANKS:
        for pin_index, member in enumerate(bank.members):
            if member == position:
                return ExpanderChannel(bank, pin_index)
    raise ValueError(
        f"invalid square coordinates {(position.file_index, position.rank)}"
    )
