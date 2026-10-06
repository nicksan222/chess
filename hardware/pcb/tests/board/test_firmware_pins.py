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
