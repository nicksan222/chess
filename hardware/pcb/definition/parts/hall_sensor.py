"""KiCad footprint and approved PCB binding for hall sensor."""

import pcbnew

from pcb.definition.parts.land_patterns import courtyard_for, footprint, pad
from pcb.definition.parts.part import PcbPart
from shared.components import HALL_SENSOR
from shared.electronics.hall_sensor import HallSensorComponent as HallSensor
from shared.electronics.hall_sensor import HallSensorPin

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

HALL_SENSOR_PART = PcbPart(
    HALL_SENSOR,
    HallSensor,
    HALLSENSOR_FOOTPRINT,
    "HALL",
    "DRV5032FC",
    "Omnipolar active-low Hall-effect square sensor",
)
