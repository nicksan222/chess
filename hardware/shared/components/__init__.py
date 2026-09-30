"""Approved physical products shared by PCB, CAD, and purchasing."""

from .ahct125 import AHCT125
from .barrel_jack import BARREL_JACK
from .button import BUTTON
from .cap_10u import CAP_10U
from .cap_100n import CAP_100N
from .cap_1000u import CAP_1000U
from .fuse_2a import FUSE_2A
from .hall_sensor import HALL_SENSOR
from .micro_sd import MICRO_SD
from .oled_header import OLED_HEADER
from .oled_module import OLED_MODULE
from .pi_zero_2_w import PI_ZERO_2_W
from .pi_zero_header import PI_ZERO_HEADER
from .power_supply import POWER_SUPPLY
from .power_switch import POWER_SWITCH
from .res_4k7 import RES_4K7
from .sk9822 import SK9822
from .spec import ComponentSpec, part
from .tca9554 import TCA9554
from .test_point import TEST_POINT
from .tvs_6v8 import TVS_6V8

APPROVED_COMPONENTS = (
    SK9822,
    HALL_SENSOR,
    TCA9554,
    AHCT125,
    CAP_100N,
    CAP_10U,
    CAP_1000U,
    RES_4K7,
    BUTTON,
    PI_ZERO_HEADER,
    OLED_HEADER,
    FUSE_2A,
    BARREL_JACK,
    TVS_6V8,
    POWER_SWITCH,
    TEST_POINT,
    PI_ZERO_2_W,
    OLED_MODULE,
    POWER_SUPPLY,
    MICRO_SD,
)

_component_keys = [spec.key for spec in APPROVED_COMPONENTS]
if len(_component_keys) != len(set(_component_keys)):
    raise ValueError("Approved component keys must be unique")

COMPONENTS = {spec.key: spec for spec in APPROVED_COMPONENTS}

__all__ = (
    "AHCT125",
    "APPROVED_COMPONENTS",
    "BARREL_JACK",
    "BUTTON",
    "CAP_10U",
    "CAP_100N",
    "CAP_1000U",
    "COMPONENTS",
    "FUSE_2A",
    "HALL_SENSOR",
    "MICRO_SD",
    "OLED_HEADER",
    "OLED_MODULE",
    "PI_ZERO_2_W",
    "PI_ZERO_HEADER",
    "POWER_SUPPLY",
    "POWER_SWITCH",
    "RES_4K7",
    "SK9822",
    "TCA9554",
    "TEST_POINT",
    "TVS_6V8",
    "ComponentSpec",
    "part",
)
