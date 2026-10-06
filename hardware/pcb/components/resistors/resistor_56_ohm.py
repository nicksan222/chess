"""Yageo RC0603FR-0756RL: the board's 56 ohm, 1% LED data resistor."""

from pcb.harness import (
    BoardRegistry,
    ComponentDefinition,
    Courtyard,
    LandPattern,
    Net,
    Pad,
    Placement,
    Point,
    Product,
)
from pcb.harness.components.resistor import Resistor, ResistorPin
from shared.components.res_56 import RES_56

# Yageo chip resistor mounting V.10 (2018-02-13), p4 Table 1, 0603:
# 0.9 mm land length, 0.8 mm width and 0.8 mm gap. The courtyard
# includes the production board's 0.25 mm margin around the pads/body.
RES_56_DEFINITION = ComponentDefinition(
    product=Product(
        key=RES_56.key,
        manufacturer=RES_56.manufacturer,
        part_number=RES_56.mpn,
        package=RES_56.package,
        body_mm=RES_56.require_body_mm(),
        datasheet=RES_56.datasheet,
    ),
    pin_type=ResistorPin,
    courtyard=Courtyard(3.1, 1.3),
    land_pattern=LandPattern(
        ResistorPin,
        (
            Pad(
                ResistorPin.TERMINAL_A,
                Point(-0.85, 0),
                0.9,
                0.8,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                ResistorPin.TERMINAL_B,
                Point(0.85, 0),
                0.9,
                0.8,
                solder_mask_margin_mm=0.05,
            ),
        ),
    ),
)


class Resistor56Ohm(Resistor):
    """Place this exact part; its value and package cannot be selected by callers."""

    def __init__(
        self,
        registry: BoardRegistry,
        *,
        reference: str,
        placement: Placement,
        purpose: str,
        terminal_a: Net,
        terminal_b: Net,
    ) -> None:
        super().__init__(
            registry=registry,
            reference=reference,
            definition=RES_56_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                ResistorPin.TERMINAL_A: terminal_a,
                ResistorPin.TERMINAL_B: terminal_b,
            },
            resistance_ohms=56,
            tolerance_percent=1,
        )
