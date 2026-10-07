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
    PackageClearance,
    PackagePath,
    PackageRouting,
    PackageVia,
    Pad,
    PadShape,
    Placement,
    Point,
    Product,
)
from shared.components import EFUSE
from shared.electronics.efuse import EfusePin

# Bar contacts require two necks; bias contacts escape through narrow pin gaps.
# All points are package-local, so every placed fuse carries its own geometry.
PACKAGE_PATHS = (
    *(
        PackagePath(EfusePin.INPUT, tuple(Point(x, y) for x, y in points), 0.35)
        for points in (
            ((-0.26, 1.05), (-0.26, 1.4), (-0.96, 2.1), (-0.96, 3.1)),
            ((-0.26, -1.05), (-0.26, -1.4), (-0.96, -2.1), (-0.96, -2.22)),
        )
    ),
    *(
        PackagePath(EfusePin.OUTPUT, tuple(Point(x, y) for x, y in points), 0.35)
        for points in (
            ((0.26, 1.05), (0.26, 1.4), (0.96, 2.1), (0.96, 3.9)),
            ((0.26, -1.05), (0.26, -1.4), (0.96, -2.1), (0.96, -3.9)),
        )
    ),
    PackagePath(EfusePin.ENABLE_UVLO, (Point(-0.9, 0.7), Point(-1.6, 0.7)), 0.2),
    PackagePath(
        EfusePin.ENABLE_UVLO, (Point(-1.6, 0.7), Point(-2.4, 1.5)), 0.31, via=True
    ),
    PackagePath(EfusePin.OVERCURRENT_TIMER, (Point(0.9, 0.7), Point(1.4, 0.7)), 0.2),
    PackagePath(EfusePin.CURRENT_LIMIT, (Point(0.9, 0.225), Point(1.4, 0.225)), 0.2),
    PackagePath(EfusePin.GROUND, (Point(0.9, -0.225), Point(1.4, -0.225)), 0.2),
    PackagePath(EfusePin.SLEW_RATE, (Point(0.9, -0.7), Point(1.4, -0.7)), 0.2),
    PackagePath(
        EfusePin.OVERVOLTAGE_LOCKOUT, (Point(-0.9, 0.225), Point(-2.0, 0.225)), 0.2
    ),
    PackagePath(
        EfusePin.POWER_GOOD_THRESHOLD, (Point(-0.9, -0.7), Point(-1.5, -0.7)), 0.2
    ),
    PackagePath(
        EfusePin.POWER_GOOD_THRESHOLD, (Point(-1.5, -0.7), Point(-2.0, 0.225)), 0.31
    ),
)

EFUSE_DEFINITION = ComponentDefinition(
    product=Product(
        key=EFUSE.key,
        manufacturer=EFUSE.manufacturer,
        part_number=EFUSE.mpn,
        package=EFUSE.package,
        body_mm=EFUSE.require_body_mm(),
        datasheet=EFUSE.datasheet,
    ),
    routing=PackageRouting(
        paths=(
            *PACKAGE_PATHS,
            *(
                PackagePath(EfusePin.OUTPUT, (Point(0.96, y), Point(4.05, y)), 1.5)
                for y in (3.9, -3.9)
            ),
        ),
        vias=tuple(
            PackageVia(EfusePin.OUTPUT, Point(x, y))
            for y in (3.9, -3.9)
            for x in (1.65, 2.85, 4.05)
        ),
        ports=(
            ("input_north", Point(-0.96, 3.1)),
            ("input_south", Point(-0.96, -2.22)),
            ("output_north", Point(0.96, 3.9)),
            ("output_south", Point(0.96, -3.9)),
            ("enable", Point(-2.4, 1.5)),
            ("timer", Point(1.4, 0.7)),
            ("current_limit", Point(1.4, 0.225)),
            ("ground", Point(1.4, -0.225)),
            ("slew_rate", Point(1.4, -0.7)),
            ("overvoltage", Point(-2.0, 0.225)),
        ),
        clearance=PackageClearance(0.16, 0.2, 0.6),
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
