"""1.65 kohm 1 % 0.1 W thick-film resistor (RC0603FR-071K65L).

Package geometry follows the reviewed production definition for RES_1K65.
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
from shared.components import RES_1K65

RES_1K65_DEFINITION = ComponentDefinition(
    product=Product(
        key=RES_1K65.key,
        manufacturer=RES_1K65.manufacturer,
        part_number=RES_1K65.mpn,
        package=RES_1K65.package,
        body_mm=RES_1K65.require_body_mm(),
        datasheet=RES_1K65.datasheet,
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


class Resistor1Point65Kilohm(Resistor):
    """Place the approved RC0603FR-071K65L with explicitly named terminals."""

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
            definition=RES_1K65_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                ResistorPin.TERMINAL_A: terminal_a,
                ResistorPin.TERMINAL_B: terminal_b,
            },
            resistance_ohms=1650,
            tolerance_percent=1,
        )
