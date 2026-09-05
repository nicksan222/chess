"""Resolve reviewed product keys to their owning PCB component classes."""

from __future__ import annotations

from collections.abc import Callable, Mapping

from base.component import PcbComponent
from shared.components import (
    AHCT125,
    CAP_10U,
    CAP_100N,
    CAP_1000U,
    FUSE_2A,
    HALL_SENSOR,
    RES_4K7,
    SK9822,
    TCA9554,
    TEST_POINT,
    TVS_6V8,
)

from .ahct125 import Ahct125
from .barrel_jack import BarrelJack
from .capacitor import Capacitor
from .fuse import Fuse
from .hall_sensor import HallSensor
from .oled_header import OledHeader
from .power_switch import PowerSwitch
from .raspberry_pi_header import RaspberryPiHeader
from .resistor import Resistor
from .sk9822 import Sk9822
from .tactile_switch import TactileSwitch
from .tca9554 import Tca9554
from .test_point import TestPoint
from .tvs_diode import TvsDiode

ComponentFactory = Callable[[str], PcbComponent]
EscapePolicy = Callable[[str], float]

# Product identity, rather than reference-prefix guessing, selects behavior.
_MODELS: dict[str, ComponentFactory] = {
    "AHCT125": Ahct125,
    "BARREL_JACK": BarrelJack,
    "BUTTON": TactileSwitch,
    "CAP_100N": Capacitor,
    "CAP_10U": Capacitor,
    "CAP_1000U": Capacitor,
    "FUSE_2A": Fuse,
    "HALL_SENSOR": HallSensor,
    "TCA9554": Tca9554,
    "OLED_HEADER": OledHeader,
    "PI_ZERO_HEADER": RaspberryPiHeader,
    "POWER_SWITCH": PowerSwitch,
    "RES_4K7": Resistor,
    "SK9822": Sk9822,
    "TEST_POINT": TestPoint,
    "TVS_6V8": TvsDiode,
}

# Native footprints carry MPN values, so routing can dispatch to the same class
# that owns the land pattern without guessing from reference prefixes.
_HORIZONTAL_ESCAPE_MPNS = frozenset(
    spec.mpn
    for component in (Ahct125, Tca9554)
    if component.SIGNAL_ESCAPE_HORIZONTAL
    for spec in component.specs
)
_POWER_ESCAPE_BY_MPN: dict[str, tuple[float, bool]] = {
    spec.mpn: (component.POWER_ESCAPE_MM, component.POWER_ESCAPE_HORIZONTAL)
    for component in (
        Ahct125,
        Capacitor,
        Fuse,
        HallSensor,
        Resistor,
        Sk9822,
        TestPoint,
        TvsDiode,
    )
    for spec in component.specs
}
_ESCAPE_BY_MPN: dict[str, EscapePolicy] = {
    AHCT125.mpn: Ahct125.signal_escape_distance_mm,
    CAP_100N.mpn: Capacitor.signal_escape_distance_mm,
    CAP_10U.mpn: Capacitor.signal_escape_distance_mm,
    CAP_1000U.mpn: Capacitor.signal_escape_distance_mm,
    FUSE_2A.mpn: Fuse.signal_escape_distance_mm,
    HALL_SENSOR.mpn: HallSensor.signal_escape_distance_mm,
    RES_4K7.mpn: Resistor.signal_escape_distance_mm,
    SK9822.mpn: Sk9822.signal_escape_distance_mm,
    TCA9554.mpn: Tca9554.signal_escape_distance_mm,
    TEST_POINT.mpn: TestPoint.signal_escape_distance_mm,
    TVS_6V8.mpn: TvsDiode.signal_escape_distance_mm,
}


def _part_key(reference: str, entry: Mapping[str, object]) -> str:
    value = entry.get("part_key")
    if not isinstance(value, str):
        raise ValueError(f"{reference}: component has no string part_key")
    return value


def for_netlist_entry(reference: str, entry: Mapping[str, object]) -> PcbComponent:
    """Build the typed PCB specialization selected by the product contract."""
    part_key = _part_key(reference, entry)
    try:
        factory = _MODELS[part_key]
    except KeyError as error:
        raise KeyError(f"{reference}: no component model for {part_key!r}") from error
    model = factory(reference)
    if not model.supports_part_key(part_key):
        raise TypeError(f"{reference}: {type(model).__name__} does not own {part_key}")
    return model


def signal_escape_distance_mm(mpn: str, pin_number: str) -> float:
    """Ask the owning SMD component for its exact launch distance."""
    try:
        policy = _ESCAPE_BY_MPN[mpn]
    except KeyError as error:
        raise KeyError(f"no signal-escape policy for component {mpn!r}") from error
    return policy(pin_number)


def power_escape_policy(mpn: str, pin_number: str) -> tuple[float, bool]:
    """Return the owning component's power launch distance and axis policy."""
    if mpn == TCA9554.mpn:
        return (Tca9554.signal_escape_distance_mm(pin_number), True)
    try:
        return _POWER_ESCAPE_BY_MPN[mpn]
    except KeyError as error:
        raise KeyError(f"no power-escape policy for component {mpn!r}") from error


def uses_horizontal_signal_escape(mpn: str) -> bool:
    """Whether a dense component must launch perpendicular to its pin row."""
    return mpn in _HORIZONTAL_ESCAPE_MPNS


def known_part_keys() -> frozenset[str]:
    return frozenset(_MODELS)
