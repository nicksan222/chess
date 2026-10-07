"""560 uF 10 V low-ESR electrolytic (10ZLJ560M8X11.5).

Package geometry follows the reviewed production definition for CAP_560U.
Electrical simulation is unavailable unless a model is explicitly declared.
"""

from enum import StrEnum

from pcb.harness import (
    BoardComponent,
    BoardRegistry,
    ComponentDefinition,
    Courtyard,
    LandPattern,
    ModelParameter,
    Net,
    NoConnect,
    Pad,
    PadKind,
    PadShape,
    Placement,
    Point,
    Product,
    SpiceModel,
)
from shared.components import CAP_560U


class PolarizedCapacitorPin(StrEnum):
    """Pin 1 is positive; pin 2 is negative on this radial electrolytic."""

    POSITIVE = "1"
    NEGATIVE = "2"


CAP_560U_DEFINITION = ComponentDefinition(
    product=Product(
        key=CAP_560U.key,
        manufacturer=CAP_560U.manufacturer,
        part_number=CAP_560U.mpn,
        package=CAP_560U.package,
        body_mm=CAP_560U.require_body_mm(),
        datasheet=CAP_560U.datasheet,
    ),
    pin_type=PolarizedCapacitorPin,
    courtyard=Courtyard(9.0, 9.0),
    # Ideal capacitance only: no ESR, leakage or reverse-voltage behavior.
    spice_model=SpiceModel(
        "capacitor",
        (PolarizedCapacitorPin.POSITIVE, PolarizedCapacitorPin.NEGATIVE),
        (ModelParameter("capacitance", 560e-6, "farad"),),
    ),
    land_pattern=LandPattern(
        PolarizedCapacitorPin,
        (
            Pad(
                PolarizedCapacitorPin.NEGATIVE,
                Point(1.75, -0.0),
                1.7,
                1.7,
                shape=PadShape.CIRCLE,
                kind=PadKind.THROUGH_HOLE,
                drill_mm=0.9,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                PolarizedCapacitorPin.POSITIVE,
                Point(-1.75, -0.0),
                1.7,
                1.7,
                shape=PadShape.RECTANGLE,
                kind=PadKind.THROUGH_HOLE,
                drill_mm=0.9,
                solder_mask_margin_mm=0.05,
            ),
        ),
    ),
)


class PolarizedCapacitor560Microfarad(BoardComponent[PolarizedCapacitorPin]):
    """Place the approved 10ZLJ560M8X11.5 with explicitly named terminals."""

    def __init__(
        self,
        registry: BoardRegistry,
        *,
        reference: str,
        placement: Placement,
        purpose: str,
        positive: Net | NoConnect,
        negative: Net | NoConnect,
    ) -> None:
        super().__init__(
            registry=registry,
            reference=reference,
            definition=CAP_560U_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                PolarizedCapacitorPin.POSITIVE: positive,
                PolarizedCapacitorPin.NEGATIVE: negative,
            },
        )
