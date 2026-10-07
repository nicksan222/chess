"""-20 V 14 mOhm P-channel MOSFET (LED rail switch) (Si4403DDY-T1-GE3).

Package geometry follows the reviewed production definition for LED_SWITCH.
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
    PackageRouting,
    Pad,
    PadShape,
    Placement,
    Point,
    Product,
)
from shared.components import LED_SWITCH
from shared.electronics.mosfet import PowerMosfetPin

LED_SWITCH_DEFINITION = ComponentDefinition(
    product=Product(
        key=LED_SWITCH.key,
        manufacturer=LED_SWITCH.manufacturer,
        part_number=LED_SWITCH.mpn,
        package=LED_SWITCH.package,
        body_mm=(
            LED_SWITCH.require_body_mm()[1],
            LED_SWITCH.require_body_mm()[0],
            LED_SWITCH.require_body_mm()[2],
        ),
        datasheet=LED_SWITCH.datasheet,
    ),
    routing=PackageRouting(
        power_mm=2.0, power_axis=EscapeAxis.HORIZONTAL, power_width_mm=0.6
    ),
    pin_type=PowerMosfetPin,
    courtyard=Courtyard(6.749, 5.5),
    land_pattern=LandPattern(
        PowerMosfetPin,
        (
            Pad(
                PowerMosfetPin.DRAIN_5,
                Point(2.5275, -1.905),
                1.194,
                0.559,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                PowerMosfetPin.DRAIN_6,
                Point(2.5275, -0.635),
                1.194,
                0.559,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                PowerMosfetPin.DRAIN_7,
                Point(2.5275, 0.635),
                1.194,
                0.559,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                PowerMosfetPin.DRAIN_8,
                Point(2.5275, 1.905),
                1.194,
                0.559,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                PowerMosfetPin.GATE,
                Point(-2.5275, -1.905),
                1.194,
                0.559,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                PowerMosfetPin.SOURCE_3,
                Point(-2.5275, -0.635),
                1.194,
                0.559,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                PowerMosfetPin.SOURCE_2,
                Point(-2.5275, 0.635),
                1.194,
                0.559,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                PowerMosfetPin.SOURCE_1,
                Point(-2.5275, 1.905),
                1.194,
                0.559,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.05,
            ),
        ),
    ),
)


class LedPowerMosfet(BoardComponent[PowerMosfetPin]):
    """Place Q1; its three source pads and four drain pads are internally joined."""

    def __init__(
        self,
        registry: BoardRegistry,
        *,
        reference: str,
        placement: Placement,
        purpose: str,
        source: Net,
        gate: Net,
        drain: Net,
    ) -> None:
        super().__init__(
            registry=registry,
            reference=reference,
            definition=LED_SWITCH_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                PowerMosfetPin.SOURCE_1: source,
                PowerMosfetPin.SOURCE_2: source,
                PowerMosfetPin.SOURCE_3: source,
                PowerMosfetPin.GATE: gate,
                PowerMosfetPin.DRAIN_5: drain,
                PowerMosfetPin.DRAIN_6: drain,
                PowerMosfetPin.DRAIN_7: drain,
                PowerMosfetPin.DRAIN_8: drain,
            },
        )
