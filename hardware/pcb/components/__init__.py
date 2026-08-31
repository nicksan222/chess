"""Semantic board-component models.

Each physical component type owns a class and pin enum in its own module. Board
routing uses these models rather than unlabelled ``(reference, pin)`` strings.
"""

from .ahct125 import Ahct125, Ahct125Pin, LED_LEVEL_SHIFTER
from .barrel_jack import BarrelJack, BarrelJackPad, BarrelJackPin, DC_INPUT_JACK
from .base import BoardComponent, ComponentReference, Endpoint
from .capacitor import Capacitor, CapacitorPin
from .catalog import for_netlist_entry, known_part_keys
from .dip_socket import Dip14Socket, Dip28Socket
from .fuse_holder import FuseHolder, FuseHolderPin, INPUT_FUSE
from .mcp23017 import Mcp23017, Mcp23017Pin
from .oled_header import DISPLAY_HEADER, OledHeader, OledHeaderPin
from .power_switch import MAIN_POWER_SWITCH, PowerSwitch, PowerSwitchPin
from .raspberry_pi_header import (
    HOST_GPIO_HEADER,
    RaspberryPiHeader,
    RaspberryPiHeaderPin,
)
from .reed_switch import ReedSwitch, ReedSwitchPin
from .resistor import Resistor, ResistorPin
from .sk9822 import Sk9822, Sk9822Pin
from .tactile_switch import TactileSwitch, TactileSwitchPad, TactileSwitchPin
from .test_point import TestPoint, TestPointPin
from .tvs_diode import INPUT_TVS, TvsDiode, TvsDiodePin

__all__ = [
    "Ahct125",
    "Ahct125Pin",
    "BarrelJack",
    "BarrelJackPad",
    "BarrelJackPin",
    "BoardComponent",
    "Capacitor",
    "CapacitorPin",
    "ComponentReference",
    "DC_INPUT_JACK",
    "DISPLAY_HEADER",
    "Dip14Socket",
    "Dip28Socket",
    "Endpoint",
    "FuseHolder",
    "FuseHolderPin",
    "HOST_GPIO_HEADER",
    "INPUT_FUSE",
    "INPUT_TVS",
    "LED_LEVEL_SHIFTER",
    "MAIN_POWER_SWITCH",
    "Mcp23017",
    "Mcp23017Pin",
    "OledHeader",
    "OledHeaderPin",
    "PowerSwitch",
    "PowerSwitchPin",
    "RaspberryPiHeader",
    "RaspberryPiHeaderPin",
    "ReedSwitch",
    "ReedSwitchPin",
    "Resistor",
    "ResistorPin",
    "Sk9822",
    "Sk9822Pin",
    "TactileSwitch",
    "TactileSwitchPad",
    "TactileSwitchPin",
    "TestPoint",
    "TestPointPin",
    "TvsDiode",
    "TvsDiodePin",
    "for_netlist_entry",
    "known_part_keys",
]
