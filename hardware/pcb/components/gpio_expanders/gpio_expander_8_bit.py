"""8-bit I2C GPIO expander with input pull-ups (TCA9554DWR).

Package geometry follows the reviewed production definition for TCA9554.
The declared model covers the eight pulled-up sensing inputs.
"""

from pcb.harness import (
    BoardComponent,
    BoardRegistry,
    ComponentDefinition,
    Courtyard,
    EscapeAxis,
    LandPattern,
    ModelParameter,
    Net,
    NoConnect,
    PackageRouting,
    Pad,
    PadShape,
    Placement,
    Point,
    Product,
    SpiceModel,
)
from shared.components import TCA9554
from shared.electronics.tca9554 import Tca9554Pin

TCA9554_DEFINITION = ComponentDefinition(
    product=Product(
        key=TCA9554.key,
        manufacturer=TCA9554.manufacturer,
        part_number=TCA9554.mpn,
        package=TCA9554.package,
        body_mm=TCA9554.require_body_mm(),
        datasheet=TCA9554.datasheet,
    ),
    pin_type=Tca9554Pin,
    courtyard=Courtyard(11.8, 11.0),
    routing=PackageRouting(
        signal_axis=EscapeAxis.HORIZONTAL,
        signal_by_pin=tuple((str(pin), 2.0 + (int(pin) - 1) % 4) for pin in Tca9554Pin),
        power_axis=EscapeAxis.HORIZONTAL,
        power_by_pin=tuple(
            (str(pin), 0.0 if str(pin) in ("8", "16") else 2.0 + (int(pin) - 1) % 4)
            for pin in Tca9554Pin
        ),
    ),
    # TCA9554 SCPS233E §8.3: typical input pull-up 100 kOhm;
    # §6.5: high input leakage <= 1 uA. This is the input sensing model,
    # not an I2C protocol or output-driver model.
    spice_model=SpiceModel(
        "input_pullup_bank",
        (
            Tca9554Pin.SUPPLY,
            Tca9554Pin.GROUND,
            Tca9554Pin.P0,
            Tca9554Pin.P1,
            Tca9554Pin.P2,
            Tca9554Pin.P3,
            Tca9554Pin.P4,
            Tca9554Pin.P5,
            Tca9554Pin.P6,
            Tca9554Pin.P7,
        ),
        (
            ModelParameter("pullup_resistance", 100e3, "ohm"),
            ModelParameter("input_leakage", 1e-6, "ampere"),
        ),
    ),
    land_pattern=LandPattern(
        Tca9554Pin,
        (
            Pad(
                Tca9554Pin.P4,
                Point(4.65, -4.445),
                2.0,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Tca9554Pin.P5,
                Point(4.65, -3.175),
                2.0,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Tca9554Pin.P6,
                Point(4.65, -1.904999),
                2.0,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Tca9554Pin.P7,
                Point(4.65, -0.634999),
                2.0,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Tca9554Pin.INTERRUPT,
                Point(4.65, 0.635),
                2.0,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Tca9554Pin.I2C_CLOCK,
                Point(4.65, 1.905),
                2.0,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Tca9554Pin.I2C_DATA,
                Point(4.65, 3.175),
                2.0,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Tca9554Pin.SUPPLY,
                Point(4.65, 4.445),
                2.0,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Tca9554Pin.GROUND,
                Point(-4.65, -4.445),
                2.0,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Tca9554Pin.P3,
                Point(-4.65, -3.175),
                2.0,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Tca9554Pin.P2,
                Point(-4.65, -1.904999),
                2.0,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Tca9554Pin.P1,
                Point(-4.65, -0.634999),
                2.0,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Tca9554Pin.P0,
                Point(-4.65, 0.635),
                2.0,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Tca9554Pin.ADDRESS_2,
                Point(-4.65, 1.905),
                2.0,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Tca9554Pin.ADDRESS_1,
                Point(-4.65, 3.175),
                2.0,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Tca9554Pin.ADDRESS_0,
                Point(-4.65, 4.445),
                2.0,
                0.6,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.05,
            ),
        ),
    ),
)


class GpioExpander8Bit(BoardComponent[Tca9554Pin]):
    """Place the approved TCA9554DWR with explicitly named terminals."""

    def __init__(
        self,
        registry: BoardRegistry,
        *,
        reference: str,
        placement: Placement,
        purpose: str,
        address_0: Net | NoConnect,
        address_1: Net | NoConnect,
        address_2: Net | NoConnect,
        p0: Net | NoConnect,
        p1: Net | NoConnect,
        p2: Net | NoConnect,
        p3: Net | NoConnect,
        ground: Net | NoConnect,
        p4: Net | NoConnect,
        p5: Net | NoConnect,
        p6: Net | NoConnect,
        p7: Net | NoConnect,
        interrupt: Net | NoConnect,
        i2c_clock: Net | NoConnect,
        i2c_data: Net | NoConnect,
        supply: Net | NoConnect,
    ) -> None:
        super().__init__(
            registry=registry,
            reference=reference,
            definition=TCA9554_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                Tca9554Pin.ADDRESS_0: address_0,
                Tca9554Pin.ADDRESS_1: address_1,
                Tca9554Pin.ADDRESS_2: address_2,
                Tca9554Pin.P0: p0,
                Tca9554Pin.P1: p1,
                Tca9554Pin.P2: p2,
                Tca9554Pin.P3: p3,
                Tca9554Pin.GROUND: ground,
                Tca9554Pin.P4: p4,
                Tca9554Pin.P5: p5,
                Tca9554Pin.P6: p6,
                Tca9554Pin.P7: p7,
                Tca9554Pin.INTERRUPT: interrupt,
                Tca9554Pin.I2C_CLOCK: i2c_clock,
                Tca9554Pin.I2C_DATA: i2c_data,
                Tca9554Pin.SUPPLY: supply,
            },
        )
