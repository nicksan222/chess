"""Explicit registry of approved native PCB parts.

Role: `PCB_PARTS` maps each approved product key to its checked `PcbPart` binding. The
list is explicit (not discovered) so adding a part is a visible edit here, and
`tests/board/test_land_patterns.py` requires every entry to have a cited land row.
Schematic generation, validation and tests read this registry.
"""

from pcb.definition.parts.ahct125 import AHCT125_PART
from pcb.definition.parts.button import (
    BUTTON_PART,
)
from pcb.definition.parts.capacitors import (
    CAP_1N_PART,
    CAP_1U_PART,
    CAP_10N_PART,
    CAP_10U_PART,
    CAP_100N_PART,
    CAP_560U_PART,
)
from pcb.definition.parts.efuse import EFUSE_PART
from pcb.definition.parts.fuse import FUSE_2A_PART
from pcb.definition.parts.hall_sensor import HALL_SENSOR_PART
from pcb.definition.parts.led_switch import (
    LED_ENABLE_GATE_PART,
    LED_SWITCH_DRIVER_PART,
    LED_SWITCH_PART,
)
from pcb.definition.parts.oled_header import OLED_HEADER_PART
from pcb.definition.parts.power_header import POWER_HEADER_PART
from pcb.definition.parts.raspberry_pi_header import (
    PI_ZERO_HEADER_PART,
)
from pcb.definition.parts.resistor import (
    RES_1K65_PART,
    RES_1K_PART,
    RES_10K_PART,
    RES_56_PART,
    RES_100K_PART,
    RES_169K_PRECISION_PART,
    RES_261K_PART,
    RES_604K_PRECISION_PART,
)
from pcb.definition.parts.sk9822 import SK9822_PART
from pcb.definition.parts.tca9554 import (
    TCA9554_PART,
)
from pcb.definition.parts.test_point import TEST_POINT_PART
from pcb.definition.parts.tvs_diode import TVS_12V0_PART

_PCB_PART_ENTRIES = (
    AHCT125_PART,
    BUTTON_PART,
    CAP_100N_PART,
    CAP_10U_PART,
    CAP_560U_PART,
    FUSE_2A_PART,
    HALL_SENSOR_PART,
    TCA9554_PART,
    OLED_HEADER_PART,
    PI_ZERO_HEADER_PART,
    POWER_HEADER_PART,
    RES_1K_PART,
    RES_10K_PART,
    RES_100K_PART,
    LED_SWITCH_PART,
    LED_SWITCH_DRIVER_PART,
    LED_ENABLE_GATE_PART,
    SK9822_PART,
    TEST_POINT_PART,
    TVS_12V0_PART,
    EFUSE_PART,
    RES_1K65_PART,
    RES_56_PART,
    RES_261K_PART,
    RES_604K_PRECISION_PART,
    RES_169K_PRECISION_PART,
    CAP_10N_PART,
    CAP_1N_PART,
    CAP_1U_PART,
)
# Duplicate product keys would let one binding silently shadow another, so refuse them.
PCB_PARTS = {part.spec.key: part for part in _PCB_PART_ENTRIES}
if len(PCB_PARTS) != len(_PCB_PART_ENTRIES):
    raise ValueError("PCB part keys must be unique")
