"""4-pin 3.96 mm locking side-entry power-entry header (B4PS-VH).

Package geometry follows the reviewed production definition for POWER_HEADER.
Electrical simulation is unavailable unless a model is explicitly declared.
"""

from pcb.harness import (
    BoardComponent,
    BoardRegistry,
    ComponentDefinition,
    Courtyard,
    LandPattern,
    MatedZone,
    Net,
    NoConnect,
    Pad,
    PadKind,
    PadShape,
    Placement,
    Point,
    Product,
)
from shared.components import POWER_HEADER
from shared.components.power_header import POWER_HEADER_MATED_ZONES
from shared.electronics.power_header import PowerHeaderPin

POWER_HEADER_DEFINITION = ComponentDefinition(
    product=Product(
        key=POWER_HEADER.key,
        manufacturer=POWER_HEADER.manufacturer,
        part_number=POWER_HEADER.mpn,
        package=POWER_HEADER.package,
        body_mm=POWER_HEADER.require_body_mm(),
        datasheet=POWER_HEADER.datasheet,
    ),
    pin_type=PowerHeaderPin,
    courtyard=Courtyard(16.28, 11.4),
    # Mated housing and wire exit from the cited JST drawing.
    mated_zones=tuple(
        MatedZone(start, end, width, height, role=role)
        for start, end, width, height, role in POWER_HEADER_MATED_ZONES
    ),
    land_pattern=LandPattern(
        PowerHeaderPin,
        (
            Pad(
                PowerHeaderPin.RUN,
                Point(5.939999, 4.45),
                2.45,
                2.45,
                shape=PadShape.CIRCLE,
                kind=PadKind.THROUGH_HOLE,
                drill_mm=1.65,
                solder_mask_margin_mm=0.05,
                thermal_spoke_width_mm=0.75,
            ),
            Pad(
                PowerHeaderPin.FUSED_TO_SWITCH,
                Point(1.98, 4.45),
                2.45,
                2.45,
                shape=PadShape.CIRCLE,
                kind=PadKind.THROUGH_HOLE,
                drill_mm=1.65,
                solder_mask_margin_mm=0.05,
                thermal_spoke_width_mm=0.75,
            ),
            Pad(
                PowerHeaderPin.GROUND,
                Point(-1.98, 4.45),
                2.45,
                2.45,
                shape=PadShape.CIRCLE,
                kind=PadKind.THROUGH_HOLE,
                drill_mm=1.65,
                solder_mask_margin_mm=0.05,
                thermal_spoke_width_mm=0.75,
            ),
            Pad(
                PowerHeaderPin.DC_INPUT,
                Point(-5.939999, 4.45),
                2.45,
                2.45,
                shape=PadShape.RECTANGLE,
                kind=PadKind.THROUGH_HOLE,
                drill_mm=1.65,
                solder_mask_margin_mm=0.05,
                thermal_spoke_width_mm=0.75,
            ),
        ),
    ),
)


class PowerConnector4Pin(BoardComponent[PowerHeaderPin]):
    """Place the approved B4PS-VH with explicitly named terminals."""

    def __init__(
        self,
        registry: BoardRegistry,
        *,
        reference: str,
        placement: Placement,
        purpose: str,
        dc_input: Net | NoConnect,
        ground: Net | NoConnect,
        fused_to_switch: Net | NoConnect,
        run: Net | NoConnect,
    ) -> None:
        super().__init__(
            registry=registry,
            reference=reference,
            definition=POWER_HEADER_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                PowerHeaderPin.DC_INPUT: dc_input,
                PowerHeaderPin.GROUND: ground,
                PowerHeaderPin.FUSED_TO_SWITCH: fused_to_switch,
                PowerHeaderPin.RUN: run,
            },
        )
