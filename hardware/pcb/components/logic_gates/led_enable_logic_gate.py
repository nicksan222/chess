"""Configurable gate with Schmitt inputs (LED buffer enable) (SN74LVC1G97DBVR).

Package geometry follows the reviewed production definition for LED_ENABLE_GATE.
Electrical simulation is unavailable unless a model is explicitly declared.
"""

from pcb.harness import (
    BoardComponent,
    BoardRegistry,
    ComponentDefinition,
    Courtyard,
    EscapeAxis,
    LandPattern,
    Net,
    NoConnect,
    PackageRouting,
    Pad,
    PadShape,
    Placement,
    Point,
    Product,
)
from shared.components import LED_ENABLE_GATE
from shared.electronics.mosfet import LogicGatePin

LED_ENABLE_GATE_DEFINITION = ComponentDefinition(
    product=Product(
        key=LED_ENABLE_GATE.key,
        manufacturer=LED_ENABLE_GATE.manufacturer,
        part_number=LED_ENABLE_GATE.mpn,
        package=LED_ENABLE_GATE.package,
        body_mm=LED_ENABLE_GATE.require_body_mm(),
        datasheet=LED_ENABLE_GATE.datasheet,
    ),
    pin_type=LogicGatePin,
    courtyard=Courtyard(4.2, 3.55),
    routing=PackageRouting(
        power_axis=EscapeAxis.HORIZONTAL, power_by_pin=(("2", 2.4),)
    ),
    land_pattern=LandPattern(
        LogicGatePin,
        (
            Pad(
                LogicGatePin.OUTPUT,
                Point(1.3, -0.95),
                1.1,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                LogicGatePin.SUPPLY,
                Point(1.3, -0.0),
                1.1,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                LogicGatePin.INPUT_2,
                Point(1.3, 0.95),
                1.1,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                LogicGatePin.INPUT_0,
                Point(-1.3, -0.95),
                1.1,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                LogicGatePin.GROUND,
                Point(-1.3, -0.0),
                1.1,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                LogicGatePin.INPUT_1,
                Point(-1.3, 0.95),
                1.1,
                0.6,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.05,
            ),
        ),
    ),
)


class LedEnableLogicGate(BoardComponent[LogicGatePin]):
    """Place the approved SN74LVC1G97DBVR with explicitly named terminals."""

    def __init__(
        self,
        registry: BoardRegistry,
        *,
        reference: str,
        placement: Placement,
        purpose: str,
        input_1: Net | NoConnect,
        ground: Net | NoConnect,
        input_0: Net | NoConnect,
        output: Net | NoConnect,
        supply: Net | NoConnect,
        input_2: Net | NoConnect,
    ) -> None:
        super().__init__(
            registry=registry,
            reference=reference,
            definition=LED_ENABLE_GATE_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                LogicGatePin.INPUT_1: input_1,
                LogicGatePin.GROUND: ground,
                LogicGatePin.INPUT_0: input_0,
                LogicGatePin.OUTPUT: output,
                LogicGatePin.SUPPLY: supply,
                LogicGatePin.INPUT_2: input_2,
            },
        )
