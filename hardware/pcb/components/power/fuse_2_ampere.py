"""2 A very fast-acting surface-mount fuse (0453002.MR).

Package geometry follows the reviewed production definition for FUSE_2A.
Electrical simulation is unavailable unless a model is explicitly declared.
"""

from pcb.harness import (
    BoardComponent,
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
from shared.components import FUSE_2A
from shared.electronics.passives import FusePin

FUSE_2A_DEFINITION = ComponentDefinition(
    product=Product(
        key=FUSE_2A.key,
        manufacturer=FUSE_2A.manufacturer,
        part_number=FUSE_2A.mpn,
        package=FUSE_2A.package,
        body_mm=FUSE_2A.require_body_mm(),
        datasheet=FUSE_2A.datasheet,
    ),
    pin_type=FusePin,
    courtyard=Courtyard(7.37, 3.65),
    land_pattern=LandPattern(
        FusePin,
        (
            Pad(
                FusePin.FUSED_OUTPUT,
                Point(2.455, -0.0),
                1.96,
                3.15,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                FusePin.UNFUSED_INPUT,
                Point(-2.455, -0.0),
                1.96,
                3.15,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.05,
            ),
        ),
    ),
)


class Fuse2Ampere(BoardComponent[FusePin]):
    """Place the approved 0453002.MR with explicitly named terminals."""

    def __init__(
        self,
        registry: BoardRegistry,
        *,
        reference: str,
        placement: Placement,
        purpose: str,
        unfused_input: Net | NoConnect,
        fused_output: Net | NoConnect,
    ) -> None:
        super().__init__(
            registry=registry,
            reference=reference,
            definition=FUSE_2A_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                FusePin.UNFUSED_INPUT: unfused_input,
                FusePin.FUSED_OUTPUT: fused_output,
            },
        )
