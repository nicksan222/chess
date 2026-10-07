"""261 kohm 1 % 0.1 W thick-film resistor (RC0603FR-07261KL).

Package geometry follows the reviewed production definition for RES_261K.
Electrical simulation is unavailable unless a model is explicitly declared.
"""

from pcb.harness import (
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
from pcb.harness.components.resistor import Resistor, ResistorPin
from shared.components import RES_261K

RES_261K_DEFINITION = ComponentDefinition(
    product=Product(
        key=RES_261K.key,
        manufacturer=RES_261K.manufacturer,
        part_number=RES_261K.mpn,
        package=RES_261K.package,
        body_mm=RES_261K.require_body_mm(),
        datasheet=RES_261K.datasheet,
    ),
    pin_type=ResistorPin,
    courtyard=Courtyard(3.1, 1.3),
    land_pattern=LandPattern(
        ResistorPin,
        (
            Pad(
                ResistorPin.TERMINAL_B,
                Point(0.85, -0.0),
                0.9,
                0.8,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                ResistorPin.TERMINAL_A,
                Point(-0.85, -0.0),
                0.9,
                0.8,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.05,
            ),
        ),
    ),
)


class Resistor261Kilohm(Resistor):
    """Place the approved RC0603FR-07261KL with explicitly named terminals."""

    def __init__(
        self,
        registry: BoardRegistry,
        *,
        reference: str,
        placement: Placement,
        purpose: str,
        terminal_a: Net | NoConnect,
        terminal_b: Net | NoConnect,
    ) -> None:
        super().__init__(
            registry=registry,
            reference=reference,
            definition=RES_261K_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                ResistorPin.TERMINAL_A: terminal_a,
                ResistorPin.TERMINAL_B: terminal_b,
            },
            resistance_ohms=261000,
            tolerance_percent=1,
        )
