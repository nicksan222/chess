"""Approved physical products shared by PCB, CAD, and purchasing."""

from .ahct125 import AHCT125
from .barrel_jack import BARREL_JACK
from .button import BUTTON
from .cap_10u import CAP_10U
from .cap_100n import CAP_100N
from .cap_560u import CAP_560U
from .efuse import EFUSE
from .efuse_passives import (
    CAP_1N,
    CAP_1U,
    CAP_10N,
    RES_1K,
    RES_1K65,
    RES_10K,
    RES_100K,
    RES_169K_PRECISION,
    RES_261K,
    RES_604K_PRECISION,
)
from .fuse_2a import FUSE_2A
from .hall_sensor import HALL_SENSOR
from .harness import (
    OLED_HARNESS_CONTACT,
    OLED_HARNESS_HOUSING,
    OLED_HARNESS_WIRES,
    PI_MALE_HEADER,
    POWER_HARNESS_CONTACT,
    POWER_HARNESS_HOUSING,
    POWER_HARNESS_WIRES,
    ROCKER_RECEPTACLE,
)
from .led_switch import LED_ENABLE_GATE, LED_SWITCH, LED_SWITCH_DRIVER
from .micro_sd import MICRO_SD
from .oled_header import OLED_HEADER
from .oled_module import OLED_MODULE
from .pi_zero_2_w import PI_ZERO_2_W
from .pi_zero_header import PI_ZERO_HEADER
from .power_header import POWER_HEADER
from .power_supply import POWER_SUPPLY
from .power_switch import POWER_SWITCH
from .res_56 import RES_56
from .sk9822 import SK9822
from .spec import ComponentSpec, part
from .tca9554 import TCA9554
from .test_point import TEST_POINT
from .tvs_12v0 import TVS_12V0

APPROVED_COMPONENTS = (
    SK9822,
    HALL_SENSOR,
    TCA9554,
    AHCT125,
    CAP_100N,
    CAP_10U,
    CAP_560U,
    RES_1K,
    RES_56,
    BUTTON,
    PI_ZERO_HEADER,
    OLED_HEADER,
    FUSE_2A,
    BARREL_JACK,
    TVS_12V0,
    EFUSE,
    LED_SWITCH,
    LED_SWITCH_DRIVER,
    LED_ENABLE_GATE,
    RES_10K,
    RES_100K,
    RES_1K65,
    RES_261K,
    RES_604K_PRECISION,
    RES_169K_PRECISION,
    CAP_10N,
    CAP_1N,
    CAP_1U,
    POWER_SWITCH,
    POWER_HEADER,
    TEST_POINT,
    PI_ZERO_2_W,
    OLED_MODULE,
    POWER_SUPPLY,
    MICRO_SD,
    PI_MALE_HEADER,
    POWER_HARNESS_HOUSING,
    POWER_HARNESS_CONTACT,
    *POWER_HARNESS_WIRES.values(),
    ROCKER_RECEPTACLE,
    OLED_HARNESS_HOUSING,
    OLED_HARNESS_CONTACT,
    *OLED_HARNESS_WIRES.values(),
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
    "CAP_1N",
    "CAP_1U",
    "CAP_10N",
    "CAP_10U",
    "CAP_100N",
    "CAP_560U",
    "COMPONENTS",
    "EFUSE",
    "FUSE_2A",
    "HALL_SENSOR",
    "LED_ENABLE_GATE",
    "LED_SWITCH",
    "LED_SWITCH_DRIVER",
    "MICRO_SD",
    "OLED_HARNESS_CONTACT",
    "OLED_HARNESS_HOUSING",
    "OLED_HARNESS_WIRES",
    "OLED_HEADER",
    "OLED_MODULE",
    "PI_MALE_HEADER",
    "PI_ZERO_2_W",
    "PI_ZERO_HEADER",
    "POWER_HARNESS_CONTACT",
    "POWER_HARNESS_HOUSING",
    "POWER_HARNESS_WIRES",
    "POWER_HEADER",
    "POWER_SUPPLY",
    "POWER_SWITCH",
    "RES_1K",
    "RES_1K65",
    "RES_10K",
    "RES_56",
    "RES_100K",
    "RES_169K_PRECISION",
    "RES_261K",
    "RES_604K_PRECISION",
    "ROCKER_RECEPTACLE",
    "SK9822",
    "TCA9554",
    "TEST_POINT",
    "TVS_12V0",
    "ComponentSpec",
    "part",
)
