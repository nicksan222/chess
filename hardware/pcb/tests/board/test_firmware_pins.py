"""Read-only parity between firmware pin constants and the board contract.

``apps/firmware/src/hardware/pins.rs`` is hand-maintained; this test parses it
strictly and compares it with the authoritative hardware side. It never writes
or generates anything.
"""

import os
import re
import sys
import unittest
from pathlib import Path
from typing import ClassVar

from shared.electronics.raspberry_pi_header import RaspberryPiHeaderPin
from shared.panel_buttons import PANEL_BUTTONS
from shared.wiring import (
    ASSIGNED_GPIO,
    LED_EN_GPIO,
    SCL_GPIO,
    SDA_GPIO,
    SPI_CLOCK_GPIO,
    SPI_DATA_GPIO,
)

REPO_ROOT = Path(__file__).resolve().parents[4]

# Raspberry Pi 40-pin header: physical pin -> BCM GPIO number (None = power or
# ground). Hand-typed golden table from the Raspberry Pi hardware documentation,
# "GPIO and the 40-pin header" (raspberrypi.com/documentation/computers/
# raspberry-pi.html#gpio) and pinout.xyz. Pins 27/28 are the HAT ID EEPROM
# lines (ID_SD/ID_SC = GPIO0/GPIO1).
HEADER_TO_BCM: dict[str, int | None] = {
    "1": None, "2": None,
    "3": 2, "4": None,
    "5": 3, "6": None,
    "7": 4, "8": 14,
    "9": None, "10": 15,
    "11": 17, "12": 18,
    "13": 27, "14": None,
    "15": 22, "16": 23,
    "17": None, "18": 24,
    "19": 10, "20": None,
    "21": 9, "22": 25,
    "23": 11, "24": 8,
    "25": None, "26": 7,
    "27": 0, "28": 1,
    "29": 5, "30": None,
    "31": 6, "32": 12,
    "33": 13, "34": None,
    "35": 19, "36": 16,
    "37": 26, "38": 20,
    "39": None, "40": 21,
}  # fmt: skip

# Alternate-function sanity (BCM2835/BCM2710 peripherals datasheet, GPIO
# alternate function table): I2C1 = GPIO2 SDA1 / GPIO3 SCL1 (ALT0);
# SPI0 = GPIO10 MOSI / GPIO11 SCLK (ALT0).
I2C1_SDA, I2C1_SCL = 2, 3
SPI0_MOSI, SPI0_SCLK = 10, 11
# LED rail enable (net LED_EN, active high, board pull-down, default low):
# header pin 37 = BCM26, reset pull Low (BCM2835 peripherals sec. 6.2).
LED_EN_HEADER_PIN, LED_EN_BCM = "37", 26

DEFAULT_PINS_RS = REPO_ROOT / "apps/firmware/src/hardware/pins.rs"
# FIRMWARE_PINS exists only for mutation testing against a copy. It must be
# acknowledged with FIRMWARE_PINS_OVERRIDE=1 and is resolved against the repo
# root, never the working directory.
_OVERRIDE = os.environ.get("FIRMWARE_PINS")
if _OVERRIDE is not None and os.environ.get("FIRMWARE_PINS_OVERRIDE") != "1":
    raise RuntimeError("FIRMWARE_PINS requires FIRMWARE_PINS_OVERRIDE=1")
PINS_RS = (REPO_ROOT / _OVERRIDE) if _OVERRIDE else DEFAULT_PINS_RS

_BUTTON_FIELD = re.compile(r"^    pub (\w+): ButtonPin<(\d+)>,$")
_BUTTON_INIT = re.compile(r"^            (\w+): ButtonPin::new\(Button::(\w+)\),$")
_LED_FIELD = re.compile(r"^    pub enable: Pin<(\d+), (Output)>,$")
_BUS_FIELD = re.compile(r"^    pub (data|clock): Pin<(\d+), (Output|InputOutput)>,$")


def _body(source: str, header: str) -> list[str]:
    """Lines between ``header`` and its closing brace; fail if the shape moved."""
    start = source.find(header)
    if start < 0:
        raise AssertionError(f"pins.rs no longer contains {header!r}")
    end = source.find("\n}\n", start)
    if end < 0:
        raise AssertionError(f"pins.rs: {header!r} has no closing brace at column 0")
    return source[start + len(header) : end].split("\n")[1:]


def _initializer(source: str, struct: str) -> list[str]:
    """The lines of one `impl <struct>` `Self { ... }` initializer in pins.rs; fails loudly if its shape changes."""
    start = source.find(f"impl {struct} {{")
    if start < 0:
        raise AssertionError(f"pins.rs no longer contains impl {struct}")
    open_at = source.find("        Self {\n", start)
    close_at = source.find("\n        }\n", open_at)
    if open_at < 0 or close_at < 0:
        raise AssertionError(f"pins.rs: {struct}::get() initializer changed shape")
    return source[open_at:close_at].split("\n")[1:]


def _bus(source: str, struct: str) -> dict[str, tuple[int, str]]:
    """Parse a two-pin bus struct (data and clock) into {field: (GPIO number, name)}."""
    found: dict[str, tuple[int, str]] = {}
    for line in _body(source, f"pub struct {struct} {{"):
        match = _BUS_FIELD.match(line)
        if match is None:
            raise AssertionError(f"{struct}: unrecognised field line {line!r}")
        found[match.group(1)] = (int(match.group(2)), match.group(3))
    if set(found) != {"data", "clock"}:
        raise AssertionError(f"{struct}: expected data and clock, got {sorted(found)}")
    return found


def parse_led_enable(source: str) -> tuple[int, str, str]:
    """BCM, capability and boot level of the LED rail enable pin."""
    lines = [line for line in _body(source, "pub struct LEDPins {") if line]
    match = _LED_FIELD.match(lines[0]) if len(lines) == 1 else None
    if match is None:
        raise AssertionError(f"LEDPins: unexpected fields {lines!r}")
    level = re.search(
        r"^pub const LED_ENABLE_BOOT_LEVEL: Level = Level::(\w+);$",
        source,
        re.MULTILINE,
    )
    if level is None:
        raise AssertionError("pins.rs no longer declares LED_ENABLE_BOOT_LEVEL")
    return int(match.group(1)), match.group(2), level.group(1)


def parse_buttons(source: str) -> dict[str, int]:
    """Map button name (upper case, as in panel_buttons) to BCM number."""
    bcm_by_field: dict[str, int] = {}
    for line in _body(source, "pub struct GPIOPins {"):
        match = _BUTTON_FIELD.match(line)
        if match is None:
            raise AssertionError(f"GPIOPins: unrecognised field line {line!r}")
        bcm_by_field[match.group(1)] = int(match.group(2))
    variant_by_field: dict[str, str] = {}
    for line in _initializer(source, "GPIOPins"):
        match = _BUTTON_INIT.match(line)
        if match is None:
            raise AssertionError(f"GPIOPins::get: unrecognised line {line!r}")
        variant_by_field[match.group(1)] = match.group(2)
    if set(bcm_by_field) != set(variant_by_field):
        raise AssertionError("GPIOPins fields and get() initializers disagree")
    buttons = {variant_by_field[f].upper(): bcm for f, bcm in bcm_by_field.items()}
    if len(buttons) != len(bcm_by_field):
        raise AssertionError("GPIOPins maps two fields to one Button variant")
    return buttons


class FirmwarePinParityTest(unittest.TestCase):
    """Firmware pin constants against the hardware contract (read-only parse of pins.rs)."""

    buttons: ClassVar[dict[str, int]]
    i2c: ClassVar[dict[str, tuple[int, str]]]
    spi: ClassVar[dict[str, tuple[int, str]]]
