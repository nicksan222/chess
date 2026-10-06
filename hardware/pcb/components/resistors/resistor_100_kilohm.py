"""100 kohm 1 % 0.1 W thick-film resistor (RC0603FR-07100KL).

Package geometry follows the reviewed production definition for RES_100K.
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
from shared.components import RES_100K

RES_100K_DEFINITION = ComponentDefinition(
    product=Product(
        key=RES_100K.key,
        manufacturer=RES_100K.manufacturer,
        part_number=RES_100K.mpn,
        package=RES_100K.package,
        body_mm=RES_100K.require_body_mm(),
        datasheet=RES_100K.datasheet,
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


class Resistor100Kilohm(Resistor):
    """Place the approved RC0603FR-07100KL with explicitly named terminals."""

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
            definition=RES_100K_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                ResistorPin.TERMINAL_A: terminal_a,
                ResistorPin.TERMINAL_B: terminal_b,
            },
            resistance_ohms=100000,
            tolerance_percent=1,
        )
