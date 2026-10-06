"""169 kohm 0.1 % 25 ppm 0.1 W thin-film resistor (RT0603BRD07169KL).

Package geometry follows the reviewed production definition for RES_169K_PRECISION.
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
from shared.components import RES_169K_PRECISION

RES_169K_PRECISION_DEFINITION = ComponentDefinition(
    product=Product(
        key=RES_169K_PRECISION.key,
        manufacturer=RES_169K_PRECISION.manufacturer,
        part_number=RES_169K_PRECISION.mpn,
        package=RES_169K_PRECISION.package,
        body_mm=RES_169K_PRECISION.require_body_mm(),
        datasheet=RES_169K_PRECISION.datasheet,
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


class PrecisionResistor169Kilohm(Resistor):
    """Place the approved RT0603BRD07169KL with explicitly named terminals."""

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
            definition=RES_169K_PRECISION_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                ResistorPin.TERMINAL_A: terminal_a,
                ResistorPin.TERMINAL_B: terminal_b,
            },
            resistance_ohms=169000,
            tolerance_percent=0.1,
        )
