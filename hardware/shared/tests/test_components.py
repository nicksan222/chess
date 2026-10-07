"""Tests for tool-independent component contracts.

Role: the approved-product catalogue is the one place that decides what may be bought, so
these tests check its invariants: unique canonical keys, a purchasing identity (maker,
MPN, package) on every part, and body envelopes that fail at definition time rather than
produce a wrong footprint later.
"""

import unittest

from shared.components import (
    APPROVED_COMPONENTS,
    COMPONENTS,
    OLED_MODULE,
    POWER_SUPPLY,
    SK9822,
    ComponentSpec,
)
from shared.components.button import BUTTON_ACTUATOR_DIAMETER_MM, BUTTON_HOUSING_MM
from shared.components.oled_header import OLED_HEADER_MATED_ZONES
from shared.components.oled_module import (
    OLED_CONTROLLER,
    OLED_FRAME_MM,
    OLED_HEIGHT_PIXELS,
    OLED_MOUNT_HOLES_MM,
    OLED_PAD_POSITIONS_MM,
    OLED_PCB_THICKNESS_MM,
    OLED_REFERENCE_DOCUMENTS,
    OLED_SCREEN_OFFSET_MM,
    OLED_SCREEN_SIZE_MM,
    OLED_UNDERSIDE_SIZE_MM,
    OLED_WIDTH_PIXELS,
)
from shared.components.power_header import POWER_HEADER_MATED_ZONES
from shared.components.power_switch import (
    ROCKER_BODY_MM,
    ROCKER_CUTOUT_MM,
    ROCKER_FACE_MM,
    ROCKER_PANEL_RANGE_MM,
    ROCKER_TERMINAL_LENGTH_MM,
    ROCKER_TERMINAL_PITCH_MM,
    ROCKER_TERMINAL_THICKNESS_MM,
    ROCKER_TERMINAL_WIDTH_MM,
)


class ComponentsTest(unittest.TestCase):
    def test_component_keys_are_canonical(self) -> None:
        self.assertEqual(COMPONENTS[SK9822.key], SK9822)
        self.assertEqual(len(COMPONENTS), len(APPROVED_COMPONENTS))
        self.assertEqual(
            len(APPROVED_COMPONENTS),
            len({spec.key for spec in APPROVED_COMPONENTS}),
        )

    def test_every_approved_part_has_purchasing_identity(self) -> None:
        for key, spec in COMPONENTS.items():
            with self.subTest(part=key):
                self.assertTrue(spec.manufacturer)
                self.assertTrue(spec.mpn)
                self.assertTrue(spec.package)

    def test_selected_display_is_the_i2c_ssd1309_module(self) -> None:
        self.assertEqual(OLED_MODULE.manufacturer, "Qdtech / LCDWIKI")
        self.assertEqual(OLED_MODULE.mpn, "MC242GW")
        self.assertEqual(OLED_MODULE.require_body_mm(), (72.0, 43.0, 6.25))

    def test_invalid_component_envelopes_fail_at_definition_time(self) -> None:
        with self.assertRaisesRegex(ValueError, "body dimensions must be positive"):
            ComponentSpec("X", "invalid", "pkg", "maker", "mpn", (1.0, 0.0, 1.0))

    def test_required_body_dimensions_fail_clearly_when_absent(self) -> None:
        # The LED body size is a datasheet fact other domains depend on (courtyard, plate
        # pocket); pinned here so a catalogue edit is noticed.
        # Opsco SPC/SK9822-A Rev 01 p3 §4: 5.4 over leads x 5.0 x 1.6 mm.
        self.assertEqual(SK9822.require_body_mm(), (5.4, 5.0, 1.6))
        with self.assertRaisesRegex(ValueError, "POWER_SUPPLY has no body dimensions"):
            POWER_SUPPLY.require_body_mm()

    def test_supplier_geometry_lives_beside_its_approved_product(self) -> None:
        self.assertEqual(BUTTON_HOUSING_MM, (6.0, 6.0, 3.6))
        self.assertEqual(BUTTON_ACTUATOR_DIAMETER_MM, 3.5)
        self.assertEqual(OLED_SCREEN_SIZE_MM, (55.01, 27.49))
        self.assertEqual(OLED_SCREEN_OFFSET_MM, (0.005, 2.685))
        self.assertEqual(
            OLED_MOUNT_HOLES_MM,
            ((-34.0, 19.5), (34.0, 19.5), (-34.0, -19.1), (34.0, -19.1)),
        )
        self.assertEqual(OLED_PAD_POSITIONS_MM[0], (-33.5, -3.81))
        self.assertEqual(OLED_UNDERSIDE_SIZE_MM, (60.0, 35.0, 2.2))
        self.assertEqual(OLED_PCB_THICKNESS_MM, 1.2)
        self.assertEqual(OLED_FRAME_MM, (62.1, 38.8, 2.85))
        self.assertEqual((OLED_WIDTH_PIXELS, OLED_HEIGHT_PIXELS), (128, 64))
        self.assertEqual(OLED_CONTROLLER, "ssd1309")
        self.assertEqual(
            OLED_REFERENCE_DOCUMENTS,
            (
                "https://www.lcdwiki.com/res/MC242GX/2.42inch_IIC_Module_MC242GX_Schematic.pdf",
                "https://www.lcdwiki.com/res/MC242GX/2.42inch_SSD1309_Init.txt",
            ),
        )
        self.assertEqual(ROCKER_BODY_MM, (18.9, 11.6, 12.9))
        self.assertEqual(ROCKER_CUTOUT_MM, (19.4, 13.0))
        self.assertEqual(ROCKER_PANEL_RANGE_MM, (1.25, 2.0))
        self.assertEqual(ROCKER_FACE_MM, (21.0, 6.0, 15.0))
        self.assertEqual(ROCKER_TERMINAL_LENGTH_MM, 7.0)
        self.assertEqual(ROCKER_TERMINAL_PITCH_MM, 7.0)
        self.assertEqual(ROCKER_TERMINAL_WIDTH_MM, 4.8)
        self.assertEqual(ROCKER_TERMINAL_THICKNESS_MM, 0.8)

    def test_connector_mating_geometry_lives_beside_the_headers(self) -> None:
        self.assertEqual(
            OLED_HEADER_MATED_ZONES,
            ((3.24, 5.25, 6.0, 2.95, "housing"), (5.25, 7.25, 6.0, 1.95, "wire_exit")),
        )
        self.assertEqual(
            POWER_HEADER_MATED_ZONES,
            (
                (-5.45, 16.05, 15.8, 10.5, "housing"),
                (16.05, 19.55, 15.8, 10.5, "wire_exit"),
            ),
        )

    def test_discrete_harness_products_have_plain_shared_modules(self) -> None:
        from shared.components.oled_harness_contact import OLED_HARNESS_CONTACT
        from shared.components.oled_harness_housing import OLED_HARNESS_HOUSING
        from shared.components.pi_male_header import PI_MALE_HEADER
        from shared.components.power_harness_contact import POWER_HARNESS_CONTACT
        from shared.components.power_harness_housing import POWER_HARNESS_HOUSING
        from shared.components.rocker_receptacle import ROCKER_RECEPTACLE

        self.assertEqual(
            tuple(
                product.mpn
                for product in (
                    PI_MALE_HEADER,
                    POWER_HARNESS_HOUSING,
                    POWER_HARNESS_CONTACT,
                    ROCKER_RECEPTACLE,
                    OLED_HARNESS_HOUSING,
                    OLED_HARNESS_CONTACT,
                )
            ),
            (
                "PRPC020DAAN-RC",
                "VHR-4N",
                "SVH-21T-P1.1",
                "2-520275-2",
                "SHR-04V-S-B",
                "SSH-003T-P0.2-H",
            ),
        )


if __name__ == "__main__":
    unittest.main()
