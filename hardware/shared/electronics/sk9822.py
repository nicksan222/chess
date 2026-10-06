"""Shared SK9822 pin semantics and chain direction.

Role: pin names for the 5050 LED plus which pins are chain inputs and outputs, for
routing's link-endpoint ordering (`routing/policies.py`). Schematic ERC types derive
direction from the `_IN`/`_OUT` name suffix and chain wiring names the pins explicitly.
Data and clock flow in on pins 1-2 and out on pins 6-5 to the next LED.

The constants below are the firmware-facing contract for the approved Opsco
SK9822-A (SPC/SK9822-A Rev 01); firmware has no LED driver yet.
"""

from enum import StrEnum

from shared.components import SK9822
from shared.electronics.base import ElectronicComponent

# §11(1) series data: a 32-bit start frame of zeros, then per LED "111" + 5-bit
# global brightness followed by one byte each in GREEN, RED, BLUE order ("GRB
# order output"), then an end frame of ones. The sheet draws 32 end bits; each
# LED delays the data by half a clock, so the end frame must also supply N/2
# extra clocks: use `end_frame_bits(N)` (32 is exactly enough at N = 64).
FRAME_COLOUR_ORDER = ("green", "red", "blue")
START_FRAME_BITS = 32
BRIGHTNESS_LEVELS = 32  # 5-bit global brightness, §11(4).
BLANK_LED_FRAME = bytes((0xE0, 0x00, 0x00, 0x00))  # "111" + brightness 0, all off.
# §8 / §10: VDD +3.7..+5.5 V range, IC characterised at 4.5-5.5 V (the LED
# minimum this design holds), chip supply 5.0 V typical and 5.3 V maximum; IDD
# 1 mA static. Channel current: §10 says Imax 17 mA but the part name and §9 say
# "SK9822-A 18MA", so the conservative 18 mA is used (reviewer m3).
SUPPLY_RECOMMENDED_MAX_VOLTS = 5.3
SUPPLY_ABSOLUTE_MAX_VOLTS = 5.5
CHANNEL_AMPS_MAX = 0.018
SUPPLY_MIN_VOLTS = 4.5
STATIC_AMPS = 0.001
# §3 allows serial input up to 30 MHz, but §10 gives TCLKH/TCLKL only as 17 ns
# typical and TSETUP 10 ns max: the board contract is derated to 10 MHz, where
# every link's data-to-clock skew leaves the setup time with margin
# (tests/spice/test_led_lines.py; reviewer m2).
CLOCK_HZ_MAX = 10_000_000
# Power sequence (S6, user decision D1, interfaces H5/H6): the LED rail is off
# at boot (LED_EN, BCM26, held low by the board's 100 kOhm pull-down, not by
# firmware). The board keeps the SPI buffer's LED outputs Hi-Z until LED_5V is up
# (about 2-3 ms after LED_EN rises) and turns them off at once when LED_EN falls,
# so no sequence can drive the chain's inputs above its supply. Firmware must:
#   1. raise LED_EN and stream blank frames (start frame, 64 x BLANK_LED_FRAME,
#      end frame) for at least LED_ENABLE_BLANKING_S; frames sent before the
#      outputs enable are dropped, so only then send real frames;
#   2. to switch off: send a blank frame, then drop LED_EN.
# On exit or crash the kernel releases the line and the pull-down turns the rail
# off. A chain that powers up lit cannot be blanked in time (ASSUMPTION "LED
# power-up state").
LED_ENABLE_BLANKING_S = 0.010


def end_frame_bits(led_count: int) -> int:
    """End-frame length: at least 32 bits and at least N/2 clocks (reviewer m6)."""
    return max(32, -(-led_count // 2))


class Sk9822Pin(StrEnum):
    """5050 package pins, Opsco SPC/SK9822-A Rev 01 §5 (SDI CKI GND VCC CKO SDO)."""

    DATA_IN = "1"
    CLOCK_IN = "2"
    GROUND = "3"
    FIVE_VOLTS = "4"
    CLOCK_OUT = "5"
    DATA_OUT = "6"


class Sk9822Component(ElectronicComponent[Sk9822Pin]):
    pin_type = Sk9822Pin
    specs = (SK9822,)

    @classmethod
    def input_pins(cls) -> frozenset[Sk9822Pin]:
        """Pins that receive data/clock from the previous LED (or the buffer)."""
        return frozenset((Sk9822Pin.DATA_IN, Sk9822Pin.CLOCK_IN))

    @classmethod
    def output_pins(cls) -> frozenset[Sk9822Pin]:
        """Pins that forward data/clock to the next LED (unused on the last one)."""
        return frozenset((Sk9822Pin.DATA_OUT, Sk9822Pin.CLOCK_OUT))
