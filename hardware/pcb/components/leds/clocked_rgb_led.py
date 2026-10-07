"""Clocked 5050 RGB LED (SK9822-A).

Package geometry follows the reviewed production definition for SK9822.
Electrical simulation is unavailable unless a model is explicitly declared.
"""

from pcb.harness import (
    BoardComponent,
    BoardRegistry,
    ComponentDefinition,
    Courtyard,
    EscapeAxis,
    LandPattern,
    Model3D,
    Net,
    NoConnect,
    PackageRouting,
    Pad,
    PadShape,
    Placement,
    Point,
    Product,
    Solid3D,
)
from shared.components import SK9822
from shared.electronics.sk9822 import Sk9822Pin

SK9822_DEFINITION = ComponentDefinition(
    product=Product(
        key=SK9822.key,
        manufacturer=SK9822.manufacturer,
        part_number=SK9822.mpn,
        package=SK9822.package,
        body_mm=SK9822.require_body_mm(),
        datasheet=SK9822.datasheet,
    ),
    model_3d=Model3D(
        (
            Solid3D(
                "Body",
                SK9822.require_body_mm(),
                (0, 0, SK9822.require_body_mm()[2] / 2),
                (0.78, 0.86, 0.92),
            ),
        ),
        fidelity="datasheet body envelope",
    ),
    pin_type=Sk9822Pin,
    courtyard=Courtyard(7.5, 5.5),
    routing=PackageRouting(power_mm=1.25, power_axis=EscapeAxis.VERTICAL),
    land_pattern=LandPattern(
        Sk9822Pin,
        (
            Pad(
                Sk9822Pin.DATA_OUT,
                Point(-2.6, -1.6),
                1.8,
                1.2,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Sk9822Pin.CLOCK_OUT,
                Point(-2.6, -0.0),
                1.8,
                1.2,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Sk9822Pin.FIVE_VOLTS,
                Point(-2.6, 1.6),
                1.8,
                1.2,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Sk9822Pin.GROUND,
                Point(2.6, 1.6),
                1.8,
                1.2,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Sk9822Pin.CLOCK_IN,
                Point(2.6, -0.0),
                1.8,
                1.2,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Sk9822Pin.DATA_IN,
                Point(2.6, -1.6),
                1.8,
                1.2,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.05,
            ),
        ),
    ),
)


class ClockedRgbLed(BoardComponent[Sk9822Pin]):
    """Place the approved SK9822-A with explicitly named terminals."""

    def __init__(
        self,
        registry: BoardRegistry,
        *,
        reference: str,
        placement: Placement,
        purpose: str,
        data_in: Net | NoConnect,
        clock_in: Net | NoConnect,
        ground: Net | NoConnect,
        five_volts: Net | NoConnect,
        clock_out: Net | NoConnect,
        data_out: Net | NoConnect,
    ) -> None:
        super().__init__(
            registry=registry,
            reference=reference,
            definition=SK9822_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                Sk9822Pin.DATA_IN: data_in,
                Sk9822Pin.CLOCK_IN: clock_in,
                Sk9822Pin.GROUND: ground,
                Sk9822Pin.FIVE_VOLTS: five_volts,
                Sk9822Pin.CLOCK_OUT: clock_out,
                Sk9822Pin.DATA_OUT: data_out,
            },
        )
