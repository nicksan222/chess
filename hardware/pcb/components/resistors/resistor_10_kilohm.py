"""Yageo RC0603FR-0710KL: the board's 10 kilohm, 1% resistor."""

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
from shared.components.efuse_passives import RES_10K

# Yageo chip resistor mounting V.10 (2018-02-13), p4 Table 1, 0603:
# 0.9 mm land length, 0.8 mm width and 0.8 mm gap. The courtyard
# includes the production board's 0.25 mm margin around the pads/body.
RES_10K_DEFINITION = ComponentDefinition(
    product=Product(
        key=RES_10K.key,
        manufacturer=RES_10K.manufacturer,
        part_number=RES_10K.mpn,
        package=RES_10K.package,
        body_mm=RES_10K.require_body_mm(),
        datasheet=RES_10K.datasheet,
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


class Resistor10Kilohm(Resistor):
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
            definition=RES_10K_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                ResistorPin.TERMINAL_A: terminal_a,
                ResistorPin.TERMINAL_B: terminal_b,
            },
            resistance_ohms=10000,
            tolerance_percent=1,
        )
