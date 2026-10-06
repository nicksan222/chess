"""Quad 3.3 V to 5 V logic buffer (SN74AHCT125DR).

Package geometry follows the reviewed production definition for AHCT125.
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
from shared.components import AHCT125
from shared.electronics.ahct125 import Ahct125Pin

AHCT125_DEFINITION = ComponentDefinition(
    product=Product(
        key=AHCT125.key,
        manufacturer=AHCT125.manufacturer,
        part_number=AHCT125.mpn,
        package=AHCT125.package,
        body_mm=(
            AHCT125.require_body_mm()[1],
            AHCT125.require_body_mm()[0],
            AHCT125.require_body_mm()[2],
        ),
        datasheet=AHCT125.datasheet,
    ),
    pin_type=Ahct125Pin,
    courtyard=Courtyard(7.45, 9.2),
    land_pattern=LandPattern(
        Ahct125Pin,
        (
            Pad(
                Ahct125Pin.BUFFER_3_OUTPUT,
                Point(2.7, -3.81),
                1.55,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Ahct125Pin.BUFFER_3_INPUT,
                Point(2.7, -2.539999),
                1.55,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Ahct125Pin.BUFFER_3_OUTPUT_ENABLE,
                Point(2.7, -1.27),
                1.55,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Ahct125Pin.BUFFER_4_OUTPUT,
                Point(2.7, -0.0),
                1.55,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Ahct125Pin.BUFFER_4_INPUT,
                Point(2.7, 1.27),
                1.55,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Ahct125Pin.BUFFER_4_OUTPUT_ENABLE,
                Point(2.7, 2.54),
                1.55,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Ahct125Pin.SUPPLY,
                Point(2.7, 3.81),
                1.55,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Ahct125Pin.GROUND,
                Point(-2.7, -3.81),
                1.55,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Ahct125Pin.BUFFER_2_OUTPUT,
                Point(-2.7, -2.539999),
                1.55,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Ahct125Pin.BUFFER_2_INPUT,
                Point(-2.7, -1.27),
                1.55,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Ahct125Pin.BUFFER_2_OUTPUT_ENABLE,
                Point(-2.7, -0.0),
                1.55,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Ahct125Pin.BUFFER_1_OUTPUT,
                Point(-2.7, 1.27),
                1.55,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Ahct125Pin.BUFFER_1_INPUT,
                Point(-2.7, 2.54),
                1.55,
                0.6,
                shape=PadShape.OVAL,
                solder_mask_margin_mm=0.05,
            ),
            Pad(
                Ahct125Pin.BUFFER_1_OUTPUT_ENABLE,
                Point(-2.7, 3.81),
                1.55,
                0.6,
                shape=PadShape.RECTANGLE,
                solder_mask_margin_mm=0.05,
            ),
        ),
    ),
)


class LogicLevelShifter4Channel(BoardComponent[Ahct125Pin]):
    """Place the approved SN74AHCT125DR with explicitly named terminals."""

    def __init__(
        self,
        registry: BoardRegistry,
        *,
        reference: str,
        placement: Placement,
        purpose: str,
        buffer_1_output_enable: Net | NoConnect,
        buffer_1_input: Net | NoConnect,
        buffer_1_output: Net | NoConnect,
        buffer_2_output_enable: Net | NoConnect,
        buffer_2_input: Net | NoConnect,
        buffer_2_output: Net | NoConnect,
        ground: Net | NoConnect,
        buffer_3_output: Net | NoConnect,
        buffer_3_input: Net | NoConnect,
        buffer_3_output_enable: Net | NoConnect,
        buffer_4_output: Net | NoConnect,
        buffer_4_input: Net | NoConnect,
        buffer_4_output_enable: Net | NoConnect,
        supply: Net | NoConnect,
    ) -> None:
        super().__init__(
            registry=registry,
            reference=reference,
            definition=AHCT125_DEFINITION,
            placement=placement,
            purpose=purpose,
            pins={
                Ahct125Pin.BUFFER_1_OUTPUT_ENABLE: buffer_1_output_enable,
                Ahct125Pin.BUFFER_1_INPUT: buffer_1_input,
                Ahct125Pin.BUFFER_1_OUTPUT: buffer_1_output,
                Ahct125Pin.BUFFER_2_OUTPUT_ENABLE: buffer_2_output_enable,
                Ahct125Pin.BUFFER_2_INPUT: buffer_2_input,
                Ahct125Pin.BUFFER_2_OUTPUT: buffer_2_output,
                Ahct125Pin.GROUND: ground,
                Ahct125Pin.BUFFER_3_OUTPUT: buffer_3_output,
                Ahct125Pin.BUFFER_3_INPUT: buffer_3_input,
                Ahct125Pin.BUFFER_3_OUTPUT_ENABLE: buffer_3_output_enable,
                Ahct125Pin.BUFFER_4_OUTPUT: buffer_4_output,
                Ahct125Pin.BUFFER_4_INPUT: buffer_4_input,
                Ahct125Pin.BUFFER_4_OUTPUT_ENABLE: buffer_4_output_enable,
                Ahct125Pin.SUPPLY: supply,
            },
        )
