"""KiCad footprint and approved PCB binding for the DRV5032FC Hall sensor.

Role: the omnipolar, active-low, open-drain Hall switch placed once per square (64
total) to detect a magnet under a piece. The land pattern follows the TI drawing
cited below; `tests/board/test_land_patterns.py` checks it independently.
Pin identities: `shared/electronics/hall_sensor.py`.
"""

import pcbnew

from pcb.definition.parts.land_patterns import (
    add_polarity_marker,
    courtyard_for,
    footprint,
    pad,
)
from pcb.definition.parts.part import DrawingView, PcbPart
from shared.components import HALL_SENSOR
from shared.electronics.hall_sensor import HallSensorComponent as HallSensor
from shared.electronics.hall_sensor import HallSensorPin

# TI SLVSDC7H p32 DBZ0003A land pattern: 1.3 x 0.6 pads, rows 2.1 apart, 0.95 pitch.
# Pad 1 (supply) is RECT as the polarity cue; the other two are oval.
HALLSENSOR_PADS = (
    pad(HallSensorPin.SUPPLY, -1.05, 0.95, 1.3, 0.6, pcbnew.PAD_SHAPE_RECT),
    pad(HallSensorPin.ACTIVE_LOW_OUTPUT, -1.05, -0.95, 1.3, 0.6, pcbnew.PAD_SHAPE_OVAL),
    pad(HallSensorPin.GROUND, 1.05, 0.0, 1.3, 0.6, pcbnew.PAD_SHAPE_OVAL),
)

# SOT-23-3; the 2.9 x 2.8 mm body size feeds the courtyard calculation.
HALLSENSOR_FOOTPRINT = footprint(
    "SOT-23-3",
    "DRV5032FC omnipolar Hall sensor",
    HALLSENSOR_PADS,
    courtyard_for(HALLSENSOR_PADS, (2.9, 2.8)),
)

add_polarity_marker(HALLSENSOR_FOOTPRINT, "1")

HALL_SENSOR_PART = PcbPart(
    HALL_SENSOR,
    HallSensor,
    HALLSENSOR_FOOTPRINT,
    "HALL",
    "DRV5032FC",
    "Omnipolar active-low Hall-effect square sensor",
    DrawingView.MOUNTING_SIDE,
)
