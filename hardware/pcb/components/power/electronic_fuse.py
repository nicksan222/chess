"""2.7-23 V 5.5 A eFuse, reverse polarity, OVLO, circuit breaker (TPS259474ARPWR).

Package geometry follows the reviewed production definition for EFUSE.
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
from shared.components import EFUSE
from shared.electronics.efuse import EfusePin

EFUSE_DEFINITION = ComponentDefinition(
    product=Product(
        key=EFUSE.key,
        manufacturer=EFUSE.manufacturer,
        part_number=EFUSE.mpn,
        package=EFUSE.package,
        body_mm=EFUSE.require_body_mm(),
        datasheet=EFUSE.datasheet,
    ),
    pin_type=EfusePin,
    courtyard=Courtyard(2.9, 2.9),
    land_pattern=LandPattern(
        EfusePin,
        (
            Pad(
                EfusePin.OVERCURRENT_TIMER,
                Point(0.9, 0.7),
                0.6,
                0.3,
                shape=PadShape.CUSTOM,
                solder_mask_margin_mm=0.0,
                polygon=(
                    Point(-0.3, 0.0),
                    Point(-0.05, 0.0),
                    Point(-0.05, 0.5),
                    Point(-0.3, 0.5),
                ),
            ),
            Pad(
                EfusePin.CURRENT_LIMIT,
                Point(0.9, 0.225),
                0.6,
                0.25,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.0,
            ),
            Pad(
                EfusePin.GROUND,
                Point(0.9, -0.225),
                0.6,
                0.25,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.0,
            ),
            Pad(
                EfusePin.SLEW_RATE,
                Point(0.9, -0.7),
                0.6,
                0.3,
                shape=PadShape.CUSTOM,
                solder_mask_margin_mm=0.0,
                polygon=(
                    Point(-0.3, -0.0),
                    Point(-0.05, -0.0),
                    Point(-0.05, -0.5),
                    Point(-0.3, -0.5),
                ),
            ),
            Pad(
                EfusePin.OUTPUT,
                Point(0.25, -0.0),
                0.3,
                2.4,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.0,
            ),
            Pad(
                EfusePin.INPUT,
                Point(-0.25, -0.0),
                0.3,
                2.4,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.0,
            ),
            Pad(
                EfusePin.POWER_GOOD_THRESHOLD,
                Point(-0.9, -0.7),
                0.6,
                0.3,
                shape=PadShape.CUSTOM,
                solder_mask_margin_mm=0.0,
                polygon=(
                    Point(0.05, -0.0),
                    Point(0.3, -0.0),
                    Point(0.3, -0.5),
                    Point(0.05, -0.5),
                ),
            ),
            Pad(
                EfusePin.POWER_GOOD,
                Point(-0.9, -0.225),
                0.6,
                0.25,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.0,
            ),
            Pad(
                EfusePin.OVERVOLTAGE_LOCKOUT,
                Point(-0.9, 0.225),
                0.6,
                0.25,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.0,
            ),
            Pad(
                EfusePin.ENABLE_UVLO,
                Point(-0.9, 0.7),
                0.6,
                0.3,
                shape=PadShape.CUSTOM,
                solder_mask_margin_mm=0.0,
                polygon=(
                    Point(0.05, 0.0),
                    Point(0.3, 0.0),
                    Point(0.3, 0.5),
                    Point(0.05, 0.5),
                ),
            ),
        ),
    ),
)


class ElectronicFuse(BoardComponent[EfusePin]):
    """Place the approved TPS259474ARPWR with explicitly named terminals."""

    def __init__(
        self,
        registry: BoardRegistry,
        *,
        reference: str,
        placement: Placement,
        purpose: str,
        enable_uvlo: Net | NoConnect,
        overvoltage_lockout: Net | NoConnect,
        power_good: Net | NoConnect,
        power_good_threshold: Net | NoConnect,
        input: Net | NoConnect,
        output: Net | NoConnect,
        slew_rate: Net | NoConnect,
        ground: Net | NoConnect,
        current_limit: Net | NoConnect,
        overcurrent_timer: Net | NoConnect,
    ) -> None:
        super().__init__(
            registry=registry,
            reference=reference,
            definition=EFUSE_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                EfusePin.ENABLE_UVLO: enable_uvlo,
                EfusePin.OVERVOLTAGE_LOCKOUT: overvoltage_lockout,
                EfusePin.POWER_GOOD: power_good,
                EfusePin.POWER_GOOD_THRESHOLD: power_good_threshold,
                EfusePin.INPUT: input,
                EfusePin.OUTPUT: output,
                EfusePin.SLEW_RATE: slew_rate,
                EfusePin.GROUND: ground,
                EfusePin.CURRENT_LIMIT: current_limit,
                EfusePin.OVERCURRENT_TIMER: overcurrent_timer,
            },
        )
