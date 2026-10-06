"""Shared TI TPS259474ARPW eFuse pin semantics (U74, S4b input protection).

TI SLVSFC9C Table 5-1 (RPW, top view): 1 EN/UVLO, 2 OVLO, 3 PG, 4 PGTH, 5 IN, 6 OUT,
7 DVDT, 8 GND, 9 ILM, 10 ITIMER. Checked against the datasheet by
`tests/board/test_land_patterns.py`.
"""

from enum import StrEnum

from shared.components import EFUSE
from shared.electronics.base import ElectronicComponent


class EfusePin(StrEnum):
    """TPS259474 (RPW 10-pin) pins by function: enable/UVLO, over-voltage lockout, power good and its threshold, input, output, slew rate (dVdt), ground, the ILM overcurrent threshold (circuit breaker) and the overcurrent timer."""

    ENABLE_UVLO = "1"
    OVERVOLTAGE_LOCKOUT = "2"
    POWER_GOOD = "3"
    POWER_GOOD_THRESHOLD = "4"
    INPUT = "5"
    OUTPUT = "6"
    SLEW_RATE = "7"
    GROUND = "8"
    CURRENT_LIMIT = "9"
    OVERCURRENT_TIMER = "10"


class EfuseComponent(ElectronicComponent[EfusePin]):
    """Typed model of the eFuse (U74)."""

    pin_type = EfusePin
    specs = (EFUSE,)
