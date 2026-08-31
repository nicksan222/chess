"""Semantic board-component models.

Each physical component type owns a class and pin enum in its own module. Board
routing uses these models rather than unlabelled ``(reference, pin)`` strings.
"""

from .base import BoardComponent, ComponentReference, Endpoint
from .barrel_jack import BarrelJack, BarrelJackPin, DC_INPUT_JACK
from .fuse_holder import FuseHolder, FuseHolderPin, INPUT_FUSE
from .power_switch import MAIN_POWER_SWITCH, PowerSwitch, PowerSwitchPin
from .sk9822 import Sk9822, Sk9822Pin
from .tactile_switch import TactileSwitch, TactileSwitchPad, TactileSwitchPin

__all__ = [
    "BarrelJack", "BarrelJackPin", "BoardComponent", "ComponentReference",
    "DC_INPUT_JACK",
    "Endpoint", "FuseHolder", "FuseHolderPin", "INPUT_FUSE",
    "MAIN_POWER_SWITCH", "PowerSwitch", "PowerSwitchPin", "Sk9822",
    "Sk9822Pin", "TactileSwitch", "TactileSwitchPad", "TactileSwitchPin",
]
