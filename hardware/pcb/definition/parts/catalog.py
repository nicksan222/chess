"""Explicit registry of approved native PCB parts."""

from pcb.definition.parts.ahct125 import AHCT125_PART
from pcb.definition.parts.barrel_jack import BARREL_JACK_PART
from pcb.definition.parts.button import (
    BUTTON_PART,
)
from pcb.definition.parts.capacitors import (
    CAP_10U_PART,
    CAP_100N_PART,
    CAP_1000U_PART,
)
from pcb.definition.parts.fuse import FUSE_2A_PART
from pcb.definition.parts.hall_sensor import HALL_SENSOR_PART
from pcb.definition.parts.oled_header import OLED_HEADER_PART
from pcb.definition.parts.power_switch import POWER_SWITCH_PART
from pcb.definition.parts.raspberry_pi_header import (
    PI_ZERO_HEADER_PART,
)
from pcb.definition.parts.resistor import RES_4K7_PART
from pcb.definition.parts.sk9822 import SK9822_PART
from pcb.definition.parts.tca9554 import (
    TCA9554_PART,
)
from pcb.definition.parts.test_point import TEST_POINT_PART
from pcb.definition.parts.tvs_diode import TVS_6V8_PART

_PCB_PART_ENTRIES = (
    AHCT125_PART,
    BARREL_JACK_PART,
    BUTTON_PART,
    CAP_100N_PART,
    CAP_10U_PART,
    CAP_1000U_PART,
    FUSE_2A_PART,
    HALL_SENSOR_PART,
    TCA9554_PART,
    OLED_HEADER_PART,
    PI_ZERO_HEADER_PART,
    POWER_SWITCH_PART,
    RES_4K7_PART,
    SK9822_PART,
    TEST_POINT_PART,
    TVS_6V8_PART,
)
PCB_PARTS = {part.spec.key: part for part in _PCB_PART_ENTRIES}
if len(PCB_PARTS) != len(_PCB_PART_ENTRIES):
    raise ValueError("PCB part keys must be unique")
