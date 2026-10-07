"""50 V logic-level N-channel MOSFET (LED switch driver) (BSS138LT1G).

Package geometry follows the reviewed production definition for LED_SWITCH_DRIVER.
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
from shared.components import LED_SWITCH_DRIVER
from shared.electronics.mosfet import SmallMosfetPin

LED_SWITCH_DRIVER_DEFINITION = ComponentDefinition(
    product=Product(
        key=LED_SWITCH_DRIVER.key,
        manufacturer=LED_SWITCH_DRIVER.manufacturer,
        part_number=LED_SWITCH_DRIVER.mpn,
        package=LED_SWITCH_DRIVER.package,
        body_mm=LED_SWITCH_DRIVER.require_body_mm(),
        datasheet=LED_SWITCH_DRIVER.datasheet,
    ),
    pin_type=SmallMosfetPin,
    courtyard=Courtyard(3.4, 3.4),
    land_pattern=LandPattern(
        SmallMosfetPin,
        (
            Pad(
                SmallMosfetPin.DRAIN,
                Point(0.0, 0.975),
                0.56,
                0.95,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                SmallMosfetPin.SOURCE,
                Point(0.95, -0.975),
                0.56,
                0.95,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                SmallMosfetPin.GATE,
                Point(-0.95, -0.975),
                0.56,
                0.95,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.05,
            ),
        ),
    ),
)


class LedSwitchDriverMosfet(BoardComponent[SmallMosfetPin]):
    """Place the approved BSS138LT1G with explicitly named terminals."""

    def __init__(
        self,
        registry: BoardRegistry,
        *,
        reference: str,
        placement: Placement,
        purpose: str,
        gate: Net | NoConnect,
        source: Net | NoConnect,
        drain: Net | NoConnect,
    ) -> None:
        super().__init__(
            registry=registry,
            reference=reference,
            definition=LED_SWITCH_DRIVER_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                SmallMosfetPin.GATE: gate,
                SmallMosfetPin.SOURCE: source,
                SmallMosfetPin.DRAIN: drain,
            },
        )
