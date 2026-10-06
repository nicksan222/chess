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
