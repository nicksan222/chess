"""12 V standoff (13.3 V min breakdown) bidirectional TVS diode (SMBJ12CA).

Package geometry follows the reviewed production definition for TVS_12V0.
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
    PackageRouting,
    Pad,
    PadShape,
    Placement,
    Point,
    Product,
)
from shared.components import TVS_12V0
from shared.electronics.passives import TvsDiodePin

TVS_12V0_DEFINITION = ComponentDefinition(
    product=Product(
        key=TVS_12V0.key,
        manufacturer=TVS_12V0.manufacturer,
        part_number=TVS_12V0.mpn,
        package=TVS_12V0.package,
        body_mm=TVS_12V0.require_body_mm(),
        datasheet=TVS_12V0.datasheet,
    ),
    pin_type=TvsDiodePin,
    courtyard=Courtyard(7.12, 4.099998),
    routing=PackageRouting(power_width_mm=1.0, power_via_count=3),
    land_pattern=LandPattern(
        TvsDiodePin,
        (
            Pad(
                TvsDiodePin.GROUND,
                Point(2.23, -0.0),
                2.16,
                2.26,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                TvsDiodePin.PROTECTED_INPUT,
                Point(-2.23, -0.0),
                2.16,
                2.26,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.05,
            ),
        ),
    ),
)


class BidirectionalTvs12Volt(BoardComponent[TvsDiodePin]):
    """Place the approved SMBJ12CA with explicitly named terminals."""

    def __init__(
        self,
        registry: BoardRegistry,
        *,
        reference: str,
        placement: Placement,
        purpose: str,
        protected_input: Net | NoConnect,
        ground: Net | NoConnect,
    ) -> None:
        super().__init__(
            registry=registry,
            reference=reference,
            definition=TVS_12V0_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                TvsDiodePin.PROTECTED_INPUT: protected_input,
                TvsDiodePin.GROUND: ground,
            },
        )
