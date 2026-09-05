"""Semantic board-component models.

Each physical component type owns a class and pin enum in its own module. Board
routing uses these models rather than unlabelled ``(reference, pin)`` strings.
"""

from base.component import BoardComponent, ComponentPin, ComponentReference, Endpoint

from .ahct125 import LED_LEVEL_SHIFTER, Ahct125, Ahct125Pin
from .barrel_jack import DC_INPUT_JACK, BarrelJack, BarrelJackPad, BarrelJackPin
from .capacitor import Capacitor, CapacitorPin
from .catalog import for_netlist_entry, known_part_keys
from .fuse import INPUT_FUSE, Fuse, FusePin
from .hall_sensor import HallSensor, HallSensorPin
from .oled_header import DISPLAY_HEADER, OledHeader, OledHeaderPin
from .power_switch import MAIN_POWER_SWITCH, PowerSwitch, PowerSwitchPin
from .raspberry_pi_header import (
    HOST_GPIO_HEADER,
    RaspberryPiHeader,
    RaspberryPiHeaderPin,
)
from .resistor import Resistor, ResistorPin
from .sk9822 import Sk9822, Sk9822Pin
from .tactile_switch import TactileSwitch, TactileSwitchPad, TactileSwitchPin
from .tca9554 import Tca9554, Tca9554Pin
from .test_point import TestPoint, TestPointPin
from .tvs_diode import INPUT_TVS, TvsDiode, TvsDiodePin

__all__ = [
    "DC_INPUT_JACK",
    "DISPLAY_HEADER",
    "HOST_GPIO_HEADER",
    "INPUT_FUSE",
    "INPUT_TVS",
    "LED_LEVEL_SHIFTER",
    "MAIN_POWER_SWITCH",
    "Ahct125",
    "Ahct125Pin",
    "BarrelJack",
    "BarrelJackPad",
    "BarrelJackPin",
    "BoardComponent",
    "Capacitor",
    "CapacitorPin",
    "ComponentPin",
    "ComponentReference",
    "Endpoint",
    "Fuse",
    "FusePin",
    "HallSensor",
    "HallSensorPin",
    "OledHeader",
    "OledHeaderPin",
    "PowerSwitch",
    "PowerSwitchPin",
    "RaspberryPiHeader",
    "RaspberryPiHeaderPin",
    "Resistor",
    "ResistorPin",
    "Sk9822",
    "Sk9822Pin",
    "TactileSwitch",
    "TactileSwitchPad",
    "TactileSwitchPin",
    "Tca9554",
    "Tca9554Pin",
    "TestPoint",
    "TestPointPin",
    "TvsDiode",
    "TvsDiodePin",
    "for_netlist_entry",
    "known_part_keys",
]
