"""10 uF 10 V X5R MLCC (CC0805KKX5R6BB106).

Package geometry follows the reviewed production definition for CAP_10U.
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
from shared.components import CAP_10U

CAP_10U_DEFINITION = ComponentDefinition(
    product=Product(
        key=CAP_10U.key,
        manufacturer=CAP_10U.manufacturer,
        part_number=CAP_10U.mpn,
        package=CAP_10U.package,
        body_mm=CAP_10U.require_body_mm(),
        datasheet=CAP_10U.datasheet,
    ),
    pin_type=CapacitorPin,
    courtyard=Courtyard(3.1, 1.8),
    land_pattern=LandPattern(
        CapacitorPin,
        (
            Pad(
                CapacitorPin.TERMINAL_B,
                Point(0.95, -0.0),
                0.7,
                1.3,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                CapacitorPin.TERMINAL_A,
                Point(-0.95, -0.0),
                0.7,
                1.3,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.05,
            ),
        ),
    ),
)


class Capacitor10Microfarad(Capacitor):
    """Place the approved CC0805KKX5R6BB106 with explicitly named terminals."""

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
            definition=CAP_10U_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                CapacitorPin.TERMINAL_A: terminal_a,
                CapacitorPin.TERMINAL_B: terminal_b,
            },
            capacitance_farads=1e-05,
            rated_volts=10,
        )
