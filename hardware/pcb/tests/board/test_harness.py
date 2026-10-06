"""Each harness cavity mates the board pad carrying the net the harness expects.

The pad is found by where JST's drawing (hand-typed rows in test_land_patterns) puts
the circuit of that number once the connector sits at its agreed placement, not by
pad number: a part on the bottom is seen mirrored from the top. So a mirrored
footprint, a renumbered land or a harness edit each fail here.
"""

import math
import unittest

import pcbnew

from board.test_land_patterns import GOLDEN
from pcb.definition import board, native
from shared import dimensions
from shared.electronics.harness import HARNESS_PARTS, HARNESSES

TOLERANCE_MM = 0.01
KEYS = {"J4": "POWER_HEADER", "J2": "OLED_HEADER"}


def _rotate(x: float, y: float, degrees: float) -> tuple[float, float]:
    """Rotate (x, y) by `degrees` about the origin."""
    c, s = math.cos(math.radians(degrees)), math.sin(math.radians(degrees))
    return (x * c - y * s, x * s + y * c)
