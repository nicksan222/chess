"""Approved native footprint templates and component-specific routing data."""

from collections.abc import Callable

import pcbnew

from pcb.definition import rules
from pcb.definition.parts.land_patterns import (
    courtyard_for,
    footprint,
    pad,
    pin_header,
    soic,
    two_pad_axial,
    two_terminal_smd,
)
from shared.components import (
    AHCT125,
    COMPONENTS,
    HALL_SENSOR,
    TCA9554,
)
from shared.electronics import ComponentReference, EndpointResolver
from shared.electronics.ahct125 import Ahct125Component as Ahct125
from shared.electronics.ahct125 import Ahct125Pin
from shared.electronics.barrel_jack import BarrelJackComponent as BarrelJack
from shared.electronics.barrel_jack import BarrelJackPad
from shared.electronics.connectors import OledHeaderComponent as OledHeader
from shared.electronics.connectors import OledHeaderPin
from shared.electronics.hall_sensor import HallSensorComponent as HallSensor
from shared.electronics.hall_sensor import HallSensorPin
from shared.electronics.passives import CapacitorComponent as Capacitor
from shared.electronics.passives import (
    CapacitorPin,
    FusePin,
    PowerSwitchPin,
    ResistorPin,
    TvsDiodePin,
)
from shared.electronics.passives import FuseComponent as Fuse
from shared.electronics.passives import PowerSwitchComponent as PowerSwitch
from shared.electronics.passives import ResistorComponent as Resistor
from shared.electronics.passives import TvsDiodeComponent as TvsDiode
from shared.electronics.raspberry_pi_header import (
    RaspberryPiHeaderComponent as RaspberryPiHeader,
)
from shared.electronics.raspberry_pi_header import (
    RaspberryPiHeaderPin,
)
from shared.electronics.sk9822 import Sk9822Component as Sk9822
from shared.electronics.sk9822 import Sk9822Pin
from shared.electronics.tactile_switch import TactileSwitchComponent as TactileSwitch
from shared.electronics.tactile_switch import TactileSwitchPad
from shared.electronics.tca9554 import Tca9554Component as Tca9554
from shared.electronics.tca9554 import Tca9554Pin
from shared.electronics.test_point import TestPointComponent as TestPoint
from shared.electronics.test_point import TestPointPin

AHCT125_FOOTPRINT = soic(
    "SOIC-14 1.27 mm",
    "SN74AHCT125DR narrow SOIC",
    14,
    5.4,
    (6.2, 8.7),
    tuple(Ahct125Pin),
)

BARRELJACK_SLOT_MM = (1.0, 1.6)

BARRELJACK_PAD_MM = (2.0, 2.6)

BARRELJACK_PADS = (
    pad(
        BarrelJackPad.CENTRE_POSITIVE,
        0.0,
        -3.0,
        *BARRELJACK_PAD_MM,
        pcbnew.PAD_SHAPE_RECT,
        *BARRELJACK_SLOT_MM,
    ),
    pad(
        BarrelJackPad.SLEEVE_GROUND,
        0.0,
        3.0,
        *BARRELJACK_PAD_MM,
        pcbnew.PAD_SHAPE_CIRCLE,
        *BARRELJACK_SLOT_MM,
    ),
    pad(
        BarrelJackPad.SWITCHED_SLEEVE_GROUND,
        -4.7,
        0.0,
        *BARRELJACK_PAD_MM,
        pcbnew.PAD_SHAPE_CIRCLE,
        *BARRELJACK_SLOT_MM,
    ),
)

BARRELJACK_FOOTPRINT = footprint(
    "5.5x2.0 mm THT",
    "Same Sky PJ-102A 5.5 x 2.0 mm DC jack, centre positive",
    BARRELJACK_PADS,
    courtyard_for(BARRELJACK_PADS, (14.4, 11.0)),
)


CAPACITOR_0603_FOOTPRINT = two_terminal_smd(
    "0603 (1608 metric)",
    "100 nF X7R MLCC",
    1.5,
    (0.9, 0.95),
    (1.6, 0.8),
    tuple(CapacitorPin),
)

CAPACITOR_0805_FOOTPRINT = two_terminal_smd(
    "0805 (2012 metric)",
    "10 uF X5R MLCC",
    1.9,
    (1.0, 1.4),
    (2.0, 1.25),
    tuple(CapacitorPin),
)

CAPACITOR_ELECTROLYTIC_10MM = two_pad_axial(
    "radial 10 mm",
    "1000 uF radial electrolytic",
    pitch=5.0,
    lead_diameter=0.8,
    body=(10.5, 10.5),
    pin_numbers=tuple(CapacitorPin),
)

CAPACITOR_LED_BYPASS_OFFSET_MM = (0.0, -8.0)

CAPACITOR_HALL_BYPASS_OFFSET_MM = (0.0, -3.0)


FUSE_FOOTPRINT = two_terminal_smd(
    "2410 fuse",
    "5 A time-delay surface-mount fuse",
    6.6,
    (2.7, 3.2),
    (6.1, 2.7),
    tuple(FusePin),
)


HALLSENSOR_PADS = (
    pad(HallSensorPin.SUPPLY, -0.95, 0.95, 1.0, 1.1, pcbnew.PAD_SHAPE_RECT),
    pad(HallSensorPin.ACTIVE_LOW_OUTPUT, -0.95, -0.95, 1.0, 1.1, pcbnew.PAD_SHAPE_OVAL),
    pad(HallSensorPin.GROUND, 0.95, 0.0, 1.0, 1.1, pcbnew.PAD_SHAPE_OVAL),
)

HALLSENSOR_FOOTPRINT = footprint(
    "SOT-23-3",
    "DRV5032FC omnipolar Hall sensor",
    HALLSENSOR_PADS,
    courtyard_for(HALLSENSOR_PADS, (2.9, 2.8)),
)


OLEDHEADER_FOOTPRINT = pin_header(
    "1x4 2.54 mm THT",
    "Four-pin SH1106 I2C OLED module connector",
    columns=4,
    rows=1,
    pin_numbers=tuple(OledHeaderPin),
)

POWERSWITCH_FOOTPRINT = two_pad_axial(
    "SPST rocker THT",
    "Latching rocker power switch",
    pitch=12.7,
    lead_diameter=1.2,
    body=(19.5, 13.0),
    pin_numbers=tuple(PowerSwitchPin),
)

RASPBERRYPIHEADER_FOOTPRINT = pin_header(
    "2x20 2.54 mm THT",
    "Raspberry Pi Zero 2 W GPIO socket",
    columns=20,
    rows=2,
    pin_numbers=tuple(RaspberryPiHeaderPin),
)

RASPBERRYPIHEADER_BUTTON_VIA_KEEPOUT_HALF_WIDTH_MM = 1.2

RASPBERRYPIHEADER_POWER_ESCAPE_MM = 6.0

RASPBERRYPIHEADER_BUTTON_VIA_KEEPOUT_LENGTH_MM = 6.0


RESISTOR_FOOTPRINT = two_terminal_smd(
    "0603 (1608 metric)",
    "4.7 kΩ thick-film resistor",
    1.5,
    (0.9, 0.95),
    (1.6, 0.8),
    tuple(ResistorPin),
)


SK9822_BODY_MM = (5.0, 5.0)

SK9822_PAD_LONG_MM = 1.5

SK9822_PAD_SHORT_MM = 1.0

SK9822_PAD_EDGE_MM = 2.5

SK9822_SIGNAL_PITCH_MM = 1.6

SK9822_PADS = (
    pad(
        Sk9822Pin.DATA_IN,
        -SK9822_PAD_EDGE_MM,
        SK9822_SIGNAL_PITCH_MM / 2.0,
        SK9822_PAD_LONG_MM,
        SK9822_PAD_SHORT_MM,
        pcbnew.PAD_SHAPE_RECT,
    ),
    pad(
        Sk9822Pin.CLOCK_IN,
        -SK9822_PAD_EDGE_MM,
        -SK9822_SIGNAL_PITCH_MM / 2.0,
        SK9822_PAD_LONG_MM,
        SK9822_PAD_SHORT_MM,
        pcbnew.PAD_SHAPE_OVAL,
    ),
    pad(
        Sk9822Pin.DATA_OUT,
        SK9822_PAD_EDGE_MM,
        SK9822_SIGNAL_PITCH_MM / 2.0,
        SK9822_PAD_LONG_MM,
        SK9822_PAD_SHORT_MM,
        pcbnew.PAD_SHAPE_OVAL,
    ),
    pad(
        Sk9822Pin.CLOCK_OUT,
        SK9822_PAD_EDGE_MM,
        -SK9822_SIGNAL_PITCH_MM / 2.0,
        SK9822_PAD_LONG_MM,
        SK9822_PAD_SHORT_MM,
        pcbnew.PAD_SHAPE_OVAL,
    ),
    pad(
        Sk9822Pin.FIVE_VOLTS,
        0.0,
        SK9822_PAD_EDGE_MM,
        SK9822_PAD_SHORT_MM,
        SK9822_PAD_LONG_MM,
        pcbnew.PAD_SHAPE_OVAL,
    ),
    pad(
        Sk9822Pin.GROUND,
        0.0,
        -SK9822_PAD_EDGE_MM,
        SK9822_PAD_SHORT_MM,
        SK9822_PAD_LONG_MM,
        pcbnew.PAD_SHAPE_OVAL,
    ),
)

SK9822_FOOTPRINT = footprint(
    "PLCC-6 5050",
    "SK9822 clocked addressable RGB LED",
    SK9822_PADS,
    courtyard_for(SK9822_PADS, SK9822_BODY_MM),
)


TACTILESWITCH_DRILL = rules.drill_for_lead(0.7)

TACTILESWITCH_PAD = rules.pad_for_drill(TACTILESWITCH_DRILL)

TACTILESWITCH_PADS = (
    pad(
        TactileSwitchPad.SIGNAL_PRIMARY,
        -3.25,
        2.25,
        TACTILESWITCH_PAD,
        TACTILESWITCH_PAD,
        pcbnew.PAD_SHAPE_RECT,
        TACTILESWITCH_DRILL,
    ),
    pad(
        TactileSwitchPad.SIGNAL_DUPLICATE,
        -3.25,
        -2.25,
        TACTILESWITCH_PAD,
        TACTILESWITCH_PAD,
        pcbnew.PAD_SHAPE_CIRCLE,
        TACTILESWITCH_DRILL,
    ),
    pad(
        TactileSwitchPad.GROUND_PRIMARY,
        3.25,
        2.25,
        TACTILESWITCH_PAD,
        TACTILESWITCH_PAD,
        pcbnew.PAD_SHAPE_CIRCLE,
        TACTILESWITCH_DRILL,
    ),
    pad(
        TactileSwitchPad.GROUND_DUPLICATE,
        3.25,
        -2.25,
        TACTILESWITCH_PAD,
        TACTILESWITCH_PAD,
        pcbnew.PAD_SHAPE_CIRCLE,
        TACTILESWITCH_DRILL,
    ),
)

TACTILESWITCH_FOOTPRINT = footprint(
    "6x6 mm THT",
    "6 mm tactile panel switch, 9.5 mm actuator",
    TACTILESWITCH_PADS,
    courtyard_for(TACTILESWITCH_PADS, (6.2, 6.2)),
)

TACTILESWITCH_LABEL_OFFSET_MM = 6.5


TCA9554_FOOTPRINT = soic(
    "SOIC-16W 1.27 mm",
    "TCA9554DWR wide SOIC, TI DW0016A",
    16,
    9.3,
    (7.6, 10.5),
    tuple(Tca9554Pin),
    pad_size_mm=(2.0, 0.6),
)

TCA9554_BYPASS_OFFSET_MM = (8.0, 6.0)

TCA9554_SILKSCREEN_CLEARANCE_MM = 2.0


TESTPOINT_PADS = (pad(TestPointPin.PROBE, 0.0, 0.0, 2.5, 1.25, pcbnew.PAD_SHAPE_RECT),)

TESTPOINT_FOOTPRINT = footprint(
    "SMD test point",
    "Low-profile SMT probe loop",
    TESTPOINT_PADS,
    courtyard_for(TESTPOINT_PADS, (2.0, 1.2)),
)


TVSDIODE_FOOTPRINT = two_terminal_smd(
    "SMB (DO-214AA)",
    "6 V unidirectional TVS diode",
    5.1,
    (2.2, 2.4),
    (4.6, 3.6),
    tuple(TvsDiodePin),
)

DC_INPUT_JACK = BarrelJack(ComponentReference.DC_INPUT_JACK)
INPUT_FUSE = Fuse(ComponentReference.INPUT_FUSE)
MAIN_POWER_SWITCH = PowerSwitch(ComponentReference.MAIN_POWER_SWITCH)

MODELS: dict[str, Callable[[str], EndpointResolver]] = {
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

TEMPLATES = {
    "AHCT125": AHCT125_FOOTPRINT,
    "BARREL_JACK": BARRELJACK_FOOTPRINT,
    "BUTTON": TACTILESWITCH_FOOTPRINT,
    "CAP_100N": CAPACITOR_0603_FOOTPRINT,
    "CAP_10U": CAPACITOR_0805_FOOTPRINT,
    "CAP_1000U": CAPACITOR_ELECTROLYTIC_10MM,
    "FUSE_2A": FUSE_FOOTPRINT,
    "HALL_SENSOR": HALLSENSOR_FOOTPRINT,
    "TCA9554": TCA9554_FOOTPRINT,
    "OLED_HEADER": OLEDHEADER_FOOTPRINT,
    "PI_ZERO_HEADER": RASPBERRYPIHEADER_FOOTPRINT,
    "POWER_SWITCH": POWERSWITCH_FOOTPRINT,
    "RES_4K7": RESISTOR_FOOTPRINT,
    "SK9822": SK9822_FOOTPRINT,
    "TEST_POINT": TESTPOINT_FOOTPRINT,
    "TVS_6V8": TVSDIODE_FOOTPRINT,
}


SMD_MPNS = {
    COMPONENTS[key].mpn
    for key, template in TEMPLATES.items()
    if any(p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD for p in template.Pads())
}


def signal_escape_distance_mm(mpn: str, pin_number: str) -> float:
    if mpn not in SMD_MPNS:
        raise KeyError(f"no signal escape for {mpn}")
    if mpn in (AHCT125.mpn, TCA9554.mpn):
        return 2.0 + (int(pin_number) - 1) % 4
    return 3.0 if mpn == HALL_SENSOR.mpn else 2.0


def power_escape_policy(mpn: str, pin_number: str) -> tuple[float, bool]:
    if mpn not in SMD_MPNS:
        raise KeyError(f"no power escape for {mpn}")
    if mpn == TCA9554.mpn:
        return signal_escape_distance_mm(mpn, pin_number), True
    return (1.2, True) if mpn == AHCT125.mpn else (0.4, False)


def uses_horizontal_signal_escape(mpn: str) -> bool:
    return mpn in (AHCT125.mpn, TCA9554.mpn)
