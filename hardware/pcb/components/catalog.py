"""Resolve reviewed netlist entries to typed component models."""

from __future__ import annotations

from collections.abc import Mapping

from base.component import BoardComponent

from .ahct125 import Ahct125
from .barrel_jack import BarrelJack
from .capacitor import Capacitor
from .fuse import Fuse
from .hall_sensor import HallSensor
from .mcp23017 import Mcp23017
from .oled_header import OledHeader
from .power_switch import PowerSwitch
from .raspberry_pi_header import RaspberryPiHeader
from .resistor import Resistor
from .sk9822 import Sk9822
from .tactile_switch import TactileSwitch
from .test_point import TestPoint
from .tvs_diode import TvsDiode

# Product identity, rather than reference-prefix guessing, determines pinout.
_MODELS: dict[str, type[BoardComponent]] = {
    "AHCT125": Ahct125,
    "BARREL_JACK": BarrelJack,
    "BUTTON": TactileSwitch,
    "CAP_100N": Capacitor,
    "CAP_10U": Capacitor,
    "CAP_1000U": Capacitor,
    "FUSE_2A": Fuse,
    "HALL_SENSOR": HallSensor,
    "MCP23017": Mcp23017,
    "OLED_HEADER": OledHeader,
    "PI_ZERO_HEADER": RaspberryPiHeader,
    "POWER_SWITCH": PowerSwitch,
    "RES_4K7": Resistor,
    "SK9822": Sk9822,
    "TEST_POINT": TestPoint,
    "TVS_6V8": TvsDiode,
}


def for_netlist_entry(reference: str, entry: Mapping[str, object]) -> BoardComponent:
    """Build the typed model selected by a netlist component's product key."""
    part_key = entry.get("part_key")
    if not isinstance(part_key, str):
        raise ValueError(f"{reference}: component has no string part_key")
    try:
        model = _MODELS[part_key]
    except KeyError as error:
        raise KeyError(f"{reference}: no component model for {part_key!r}") from error
    return model(reference)


def known_part_keys() -> frozenset[str]:
    """Return product keys for which a typed component model exists."""
    return frozenset(_MODELS)
