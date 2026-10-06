"""Reusable electronic component definitions, independent of KiCad and CAD."""

from .ahct125 import Ahct125Component, Ahct125Pin
from .barrel_jack import BarrelJackComponent, BarrelJackPad, BarrelJackPin
from .base import (
    RETIRED_REFERENCES,
    BoundPin,
    ComponentPin,
    ComponentReference,
    ElectronicComponent,
    Endpoint,
    EndpointResolver,
)
from .connectors import OledHeaderComponent, OledHeaderPin
from .efuse import EfuseComponent, EfusePin
from .hall_sensor import HallSensorComponent, HallSensorPin
from .mosfet import (
    LogicGateComponent,
    LogicGatePin,
    PowerMosfetComponent,
    PowerMosfetPin,
    SmallMosfetComponent,
    SmallMosfetPin,
)
from .passives import (
    CapacitorComponent,
    CapacitorPin,
    FuseComponent,
    FusePin,
    PowerSwitchComponent,
    PowerSwitchPin,
    ResistorComponent,
    ResistorPin,
    TvsDiodeComponent,
    TvsDiodePin,
)
from .power_header import PowerHeaderComponent, PowerHeaderPin
from .raspberry_pi_header import (
    HeaderLegend,
    HeaderLegendEntry,
    RaspberryPiHeaderComponent,
    RaspberryPiHeaderPin,
)
from .sk9822 import Sk9822Component, Sk9822Pin
from .tactile_switch import (
    TactileSwitchComponent,
    TactileSwitchPad,
    TactileSwitchPin,
)
from .tca9554 import Tca9554Component, Tca9554Pin
from .test_point import TestPointComponent, TestPointPin

__all__ = (
    "RETIRED_REFERENCES",
    "Ahct125Component",
    "Ahct125Pin",
    "BarrelJackComponent",
    "BarrelJackPad",
    "BarrelJackPin",
    "BoundPin",
    "CapacitorComponent",
    "CapacitorPin",
    "ComponentPin",
    "ComponentReference",
    "EfuseComponent",
    "EfusePin",
    "ElectronicComponent",
    "Endpoint",
    "EndpointResolver",
    "FuseComponent",
    "FusePin",
    "HallSensorComponent",
    "HallSensorPin",
    "HeaderLegend",
    "HeaderLegendEntry",
    "LogicGateComponent",
    "LogicGatePin",
    "OledHeaderComponent",
    "OledHeaderPin",
    "PowerHeaderComponent",
    "PowerHeaderPin",
    "PowerMosfetComponent",
    "PowerMosfetPin",
    "PowerSwitchComponent",
    "PowerSwitchPin",
    "RaspberryPiHeaderComponent",
    "RaspberryPiHeaderPin",
    "ResistorComponent",
    "ResistorPin",
    "Sk9822Component",
    "Sk9822Pin",
    "SmallMosfetComponent",
    "SmallMosfetPin",
    "TactileSwitchComponent",
    "TactileSwitchPad",
    "TactileSwitchPin",
    "Tca9554Component",
    "Tca9554Pin",
    "TestPointComponent",
    "TestPointPin",
    "TvsDiodeComponent",
    "TvsDiodePin",
)
