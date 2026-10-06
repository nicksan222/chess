"""Bypass-capacitor placement and plane fanout on the routed generated board.

Supply and ground pins come from the datasheets cited in `test_land_patterns.py`
(TCA9554 16/8, SN74AHCT125 14/7, DRV5032 1/3, SK9822 4/3). The datasheets ask
for a 0.1 uF ceramic "close to" the supply pin without a number (TI SLVSDC7H §9,
SCPS233E §11; Opsco SPC/SK9822-A §12 "capacitance between beads is essential").
The stated limits below are this board's engineering rule, not datasheet values.
Each IC/LED gets its own nearest same-rail capacitor; no capacitor counts twice.
"""

import math
import os
import unittest
from pathlib import Path
from typing import ClassVar

import pcbnew

PCB_ROOT = Path(__file__).resolve().parents[2]

# part key -> (supply pad, supply net, ground pad)
SUPPLY_PINS = {
    "TCA9554": ("16", "+3V3", "8"),
    "AHCT125": ("14", "+5V", "7"),
    "HALL_SENSOR": ("1", "+3V3", "3"),
    "SK9822": ("4", "LED_5V", "3"),
    "LED_ENABLE_GATE": ("5", "+5V", "2"),
}
