"""Low-cost standard surface-mount packages used by the board."""

from __future__ import annotations

from collections.abc import Sequence

from components.ahct125 import Ahct125Pin
from components.capacitor import CapacitorPin
from components.fuse import FusePin
from components.hall_sensor import HallSensorPin
from components.mcp23017 import Mcp23017Pin
from components.test_point import TestPointPin
from components.tvs_diode import TvsDiodePin

from .base import Footprint, Pad, RECT, courtyard_for

SOIC_PIN_PITCH_MM = 1.27
SOIC_PAD_SIZE_MM = (1.55, 0.60)


def _two_terminal_smd(
    package: str,
    description: str,
    pitch_mm: float,
    pad_size_mm: tuple[float, float],
    body_size_mm: tuple[float, float],
    pin_numbers: Sequence[str],
) -> Footprint:
    """Build a symmetric two-terminal chip-component footprint."""
    if len(pin_numbers) != 2:
        raise ValueError(f"{package}: expected two pin numbers")
    width, height = pad_size_mm
    pads = (
        Pad(pin_numbers[0], -pitch_mm / 2.0, 0.0, width, height, RECT),
        Pad(pin_numbers[1], pitch_mm / 2.0, 0.0, width, height, RECT),
    )
    return Footprint(
        package,
        description,
        pads,
        courtyard_for(pads, body_size_mm),
    )


def _soic(
    package: str,
    description: str,
    ways: int,
    row_pitch_mm: float,
    body_size_mm: tuple[float, float],
    pin_numbers: Sequence[str],
) -> Footprint:
    """Build an SOIC with counter-clockwise datasheet pin numbering."""
    if ways % 2 != 0:
        raise ValueError(f"{package}: an SOIC needs an even pin count")
    if len(pin_numbers) != ways:
        raise ValueError(f"{package}: expected {ways} pin numbers")

    per_side = ways // 2
    span = (per_side - 1) * SOIC_PIN_PITCH_MM
    pad_width, pad_height = SOIC_PAD_SIZE_MM
    pads = []
    for index in range(per_side):
        pads.append(
            Pad(
                pin_numbers[index],
                -row_pitch_mm / 2.0,
                span / 2.0 - index * SOIC_PIN_PITCH_MM,
                pad_width,
                pad_height,
                RECT,
            )
        )
    for index in range(per_side):
        pads.append(
            Pad(
                pin_numbers[ways - index - 1],
                row_pitch_mm / 2.0,
                span / 2.0 - index * SOIC_PIN_PITCH_MM,
                pad_width,
                pad_height,
                RECT,
            )
        )
    finished_pads = tuple(pads)
    return Footprint(
        package,
        description,
        finished_pads,
        courtyard_for(finished_pads, body_size_mm),
    )


CAPACITOR_0603 = _two_terminal_smd(
    "0603 (1608 metric)",
    "100 nF X7R MLCC",
    1.50,
    (0.90, 0.95),
    (1.6, 0.8),
    tuple(CapacitorPin),
)
CAPACITOR_0805 = _two_terminal_smd(
    "0805 (2012 metric)",
    "10 uF X5R MLCC",
    1.90,
    (1.00, 1.40),
    (2.0, 1.25),
    tuple(CapacitorPin),
)
MCP23017_SOIC = _soic(
    "SOIC-28W 1.27 mm",
    "MCP23017-E/SO wide SOIC",
    28,
    9.40,
    (10.3, 17.9),
    tuple(Mcp23017Pin),
)
AHCT125_SOIC = _soic(
    "SOIC-14 1.27 mm",
    "SN74AHCT125DR narrow SOIC",
    14,
    5.40,
    (6.2, 8.7),
    tuple(Ahct125Pin),
)

_HALL_PADS = (
    Pad(HallSensorPin.SUPPLY, -0.95, 0.95, 1.00, 1.10, RECT),
    Pad(HallSensorPin.ACTIVE_LOW_OUTPUT, -0.95, -0.95, 1.00, 1.10, RECT),
    Pad(HallSensorPin.GROUND, 0.95, 0.0, 1.00, 1.10, RECT),
)
HALL_SOT23 = Footprint(
    "SOT-23-3",
    "DRV5032FC omnipolar Hall sensor",
    _HALL_PADS,
    courtyard_for(_HALL_PADS, (2.9, 2.8)),
)

FUSE_2410 = _two_terminal_smd(
    "2410 fuse",
    "5 A time-delay surface-mount fuse",
    6.60,
    (2.70, 3.20),
    (6.1, 2.7),
    tuple(FusePin),
)
TVS_SMB = _two_terminal_smd(
    "SMB (DO-214AA)",
    "6 V unidirectional TVS diode",
    5.10,
    (2.20, 2.40),
    (4.6, 3.6),
    tuple(TvsDiodePin),
)
_TEST_PAD = (Pad(TestPointPin.PROBE, 0.0, 0.0, 2.5, 1.25, RECT),)
TEST_POINT_SMD = Footprint(
    "SMD test point",
    "Low-profile SMT probe loop",
    _TEST_PAD,
    courtyard_for(_TEST_PAD, (2.0, 1.2)),
)
