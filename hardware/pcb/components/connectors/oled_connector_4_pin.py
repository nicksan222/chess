"""4-pin 1.0 mm side-entry header for the OLED harness (SM04B-SRSS-TB).

Package geometry follows the reviewed production definition for OLED_HEADER.
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
    PackageRouting,
    Pad,
    PadShape,
    Placement,
    Point,
    Product,
)
from shared.components import OLED_HEADER
from shared.electronics.connectors import OledHeaderPin

OLED_HEADER_DEFINITION = ComponentDefinition(
    product=Product(
        key=OLED_HEADER.key,
        manufacturer=OLED_HEADER.manufacturer,
        part_number=OLED_HEADER.mpn,
        package=OLED_HEADER.package,
        body_mm=OLED_HEADER.require_body_mm(),
        datasheet=OLED_HEADER.datasheet,
    ),
    pin_type=OledHeaderPin,
    courtyard=Courtyard(7.3, 6.175),
    routing=PackageRouting(
        signal_by_pin=tuple(
            (str(pin), 2.0 if int(pin) % 2 else 3.5) for pin in OledHeaderPin
        ),
        power_by_pin=tuple(
            (str(pin), 0.4 if int(pin) % 2 else 2.9) for pin in OledHeaderPin
        ),
    ),
    land_pattern=LandPattern(
        OledHeaderPin,
        (
            Pad(
                OledHeaderPin.MOUNTING_TAB_B,
                Point(2.8, -1.9375),
                1.2,
                1.8,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                OledHeaderPin.MOUNTING_TAB_A,
                Point(-2.8, -1.9375),
                1.2,
                1.8,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                OledHeaderPin.I2C_DATA,
                Point(1.5, 1.9375),
                0.6,
                1.55,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                OledHeaderPin.I2C_CLOCK,
                Point(0.5, 1.9375),
                0.6,
                1.55,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                OledHeaderPin.THREE_VOLTS_THREE,
                Point(-0.5, 1.9375),
                0.6,
                1.55,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                OledHeaderPin.GROUND,
                Point(-1.5, 1.9375),
                0.6,
                1.55,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.05,
            ),
        ),
    ),
)


class OledConnector4Pin(BoardComponent[OledHeaderPin]):
    """Place the approved SM04B-SRSS-TB with explicitly named terminals."""

    def __init__(
        self,
        registry: BoardRegistry,
        *,
        reference: str,
        placement: Placement,
        purpose: str,
        ground: Net | NoConnect,
        three_volts_three: Net | NoConnect,
        i2c_clock: Net | NoConnect,
        i2c_data: Net | NoConnect,
        mounting_tab_a: Net | NoConnect,
        mounting_tab_b: Net | NoConnect,
    ) -> None:
        super().__init__(
            registry=registry,
            reference=reference,
            definition=OLED_HEADER_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                OledHeaderPin.GROUND: ground,
                OledHeaderPin.THREE_VOLTS_THREE: three_volts_three,
                OledHeaderPin.I2C_CLOCK: i2c_clock,
                OledHeaderPin.I2C_DATA: i2c_data,
                OledHeaderPin.MOUNTING_TAB_A: mounting_tab_a,
                OledHeaderPin.MOUNTING_TAB_B: mounting_tab_b,
            },
        )
