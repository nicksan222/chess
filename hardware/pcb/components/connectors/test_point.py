"""2.0 mm high surface-mount test point (S1751-46R).

Package geometry follows the reviewed production definition for TEST_POINT.
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
from shared.components import TEST_POINT
from shared.electronics.test_point import TestPointPin

TEST_POINT_DEFINITION = ComponentDefinition(
    product=Product(
        key=TEST_POINT.key,
        manufacturer=TEST_POINT.manufacturer,
        part_number=TEST_POINT.mpn,
        package=TEST_POINT.package,
        body_mm=TEST_POINT.require_body_mm(),
        datasheet=TEST_POINT.datasheet,
    ),
    pin_type=TestPointPin,
    courtyard=Courtyard(3.95, 2.35),
    land_pattern=LandPattern(
        TestPointPin,
        (
            Pad(
                TestPointPin.PROBE,
                Point(0.0, -0.0),
                3.45,
                1.85,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.05,
            ),
        ),
    ),
)


class TestPoint(BoardComponent[TestPointPin]):
    """Place the approved S1751-46R with explicitly named terminals."""

    def __init__(
        self,
        registry: BoardRegistry,
        *,
        reference: str,
        placement: Placement,
        purpose: str,
        probe: Net | NoConnect,
    ) -> None:
        super().__init__(
            registry=registry,
            reference=reference,
            definition=TEST_POINT_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                TestPointPin.PROBE: probe,
            },
        )
