"""6 mm tactile switch, Ø3.5 mm round stem, 8.0 mm overall (TL1105CF100Q).

Package geometry follows the reviewed production definition for BUTTON.
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
    PadKind,
    PadShape,
    Placement,
    Point,
    Product,
)
from shared.components import BUTTON
from shared.electronics.tactile_switch import TactileSwitchPin

BUTTON_DEFINITION = ComponentDefinition(
    product=Product(
        key=BUTTON.key,
        manufacturer=BUTTON.manufacturer,
        part_number=BUTTON.mpn,
        package=BUTTON.package,
        body_mm=BUTTON.require_body_mm(),
        datasheet=BUTTON.datasheet,
    ),
    pin_type=TactileSwitchPin,
    courtyard=Courtyard(8.8, 6.8),
    land_pattern=LandPattern(
        TactileSwitchPin,
        (
            Pad(
                TactileSwitchPin.GROUND,
                Point(-3.25, -2.25),
                1.8,
                1.8,
                shape=PadShape.CIRCLE,
                kind=PadKind.THROUGH_HOLE,
                drill_mm=1.0,
                number="2b",
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                TactileSwitchPin.GROUND,
                Point(3.25, -2.25),
                1.8,
                1.8,
                shape=PadShape.CIRCLE,
                kind=PadKind.THROUGH_HOLE,
                drill_mm=1.0,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                TactileSwitchPin.SIGNAL,
                Point(3.25, 2.25),
                1.8,
                1.8,
                shape=PadShape.CIRCLE,
                kind=PadKind.THROUGH_HOLE,
                drill_mm=1.0,
                number="1b",
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                TactileSwitchPin.SIGNAL,
                Point(-3.25, 2.25),
                1.8,
                1.8,
                shape=PadShape.RECTANGLE,
                kind=PadKind.THROUGH_HOLE,
                drill_mm=1.0,
                solder_mask_margin_mm=0.05,
            ),
        ),
    ),
)


class TactileButton(BoardComponent[TactileSwitchPin]):
    """Place the approved TL1105CF100Q with explicitly named terminals."""

    def __init__(
        self,
        registry: BoardRegistry,
        *,
        reference: str,
        placement: Placement,
        purpose: str,
        signal: Net | NoConnect,
        ground: Net | NoConnect,
    ) -> None:
        super().__init__(
            registry=registry,
            reference=reference,
            definition=BUTTON_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                TactileSwitchPin.SIGNAL: signal,
                TactileSwitchPin.GROUND: ground,
            },
        )
