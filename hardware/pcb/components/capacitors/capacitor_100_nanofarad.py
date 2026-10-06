"""Yageo CC0603KRX7R9BB104: the board's 100 nF, 50 V X7R decoupling capacitor."""

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
from pcb.harness.components.capacitor import Capacitor, CapacitorPin
from shared.components.cap_100n import CAP_100N

# Match the production board's Murata JEMCGC-2701X p25 Table 2 reflow land:
# 0.65 x 0.7 mm pads with a 0.7 mm gap and 0.25 mm courtyard margin.
# Using Murata's land for this Yageo part remains an existing unverified
# assumption in definition/verification.py; no Yageo land drawing is on file.
CAP_100N_DEFINITION = ComponentDefinition(
    product=Product(
        key=CAP_100N.key,
        manufacturer=CAP_100N.manufacturer,
        part_number=CAP_100N.mpn,
        package=CAP_100N.package,
        body_mm=CAP_100N.require_body_mm(),
        datasheet=CAP_100N.datasheet,
    ),
    pin_type=CapacitorPin,
    courtyard=Courtyard(2.5, 1.3),
    land_pattern=LandPattern(
        CapacitorPin,
        (
            Pad(
                CapacitorPin.TERMINAL_A,
                Point(-0.675, 0),
                0.65,
                0.7,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                CapacitorPin.TERMINAL_B,
                Point(0.675, 0),
                0.65,
                0.7,
                solder_mask_margin_mm=0.05,
            ),
        ),
    ),
)


class Capacitor100Nanofarad(Capacitor):
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
            definition=CAP_100N_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                CapacitorPin.TERMINAL_A: terminal_a,
                CapacitorPin.TERMINAL_B: terminal_b,
            },
            capacitance_farads=100e-9,
            rated_volts=50,
        )
