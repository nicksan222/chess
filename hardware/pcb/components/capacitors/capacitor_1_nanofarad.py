"""1 nF 50 V X7R MLCC (CC0603KRX7R9BB102).

Package geometry follows the reviewed production definition for CAP_1N.
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
from pcb.harness.components.capacitor import Capacitor, CapacitorPin
from shared.components import CAP_1N

CAP_1N_DEFINITION = ComponentDefinition(
    product=Product(
        key=CAP_1N.key,
        manufacturer=CAP_1N.manufacturer,
        part_number=CAP_1N.mpn,
        package=CAP_1N.package,
        body_mm=CAP_1N.require_body_mm(),
        datasheet=CAP_1N.datasheet,
    ),
    pin_type=CapacitorPin,
    courtyard=Courtyard(2.5, 1.3),
    land_pattern=LandPattern(
        CapacitorPin,
        (
            Pad(
                CapacitorPin.TERMINAL_B,
                Point(0.675, -0.0),
                0.65,
                0.7,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                CapacitorPin.TERMINAL_A,
                Point(-0.675, -0.0),
                0.65,
                0.7,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.05,
            ),
        ),
    ),
)


class Capacitor1Nanofarad(Capacitor):
    """Place the approved CC0603KRX7R9BB102 with explicitly named terminals."""

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
            definition=CAP_1N_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                CapacitorPin.TERMINAL_A: terminal_a,
                CapacitorPin.TERMINAL_B: terminal_b,
            },
            capacitance_farads=1e-09,
            rated_volts=50,
        )
