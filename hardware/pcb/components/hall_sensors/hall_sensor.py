"""20 Hz omnipolar active-low Hall-effect sensor (DRV5032FCDBZR).

Package geometry follows the reviewed production definition for HALL_SENSOR.
Electrical simulation is unavailable unless a model is explicitly declared.
"""

from pcb.harness import (
    BoardComponent,
    BoardRegistry,
    ComponentDefinition,
    Courtyard,
    LandPattern,
    Net,
    NoConnect,
    Pad,
    PadShape,
    Placement,
    Point,
    Product,
)
from shared.components import HALL_SENSOR
from shared.electronics.hall_sensor import HallSensorPin

HALL_SENSOR_DEFINITION = ComponentDefinition(
    product=Product(
        key=HALL_SENSOR.key,
        manufacturer=HALL_SENSOR.manufacturer,
        part_number=HALL_SENSOR.mpn,
        package=HALL_SENSOR.package,
        body_mm=HALL_SENSOR.require_body_mm(),
        datasheet=HALL_SENSOR.datasheet,
    ),
    pin_type=HallSensorPin,
    courtyard=Courtyard(3.9, 3.3),
    land_pattern=LandPattern(
        HallSensorPin,
        (
            Pad(
                HallSensorPin.GROUND,
                Point(1.05, -0.0),
                1.3,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                HallSensorPin.ACTIVE_LOW_OUTPUT,
                Point(-1.05, -0.95),
                1.3,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                HallSensorPin.SUPPLY,
                Point(-1.05, 0.95),
                1.3,
                0.6,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.05,
            ),
        ),
    ),
)


class HallSensor(BoardComponent[HallSensorPin]):
    """Place the approved DRV5032FCDBZR with explicitly named terminals."""

    def __init__(
        self,
        registry: BoardRegistry,
        *,
        reference: str,
        placement: Placement,
        purpose: str,
        supply: Net | NoConnect,
        active_low_output: Net | NoConnect,
        ground: Net | NoConnect,
    ) -> None:
        super().__init__(
            registry=registry,
            reference=reference,
            definition=HALL_SENSOR_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                HallSensorPin.SUPPLY: supply,
                HallSensorPin.ACTIVE_LOW_OUTPUT: active_low_output,
                HallSensorPin.GROUND: ground,
            },
        )
