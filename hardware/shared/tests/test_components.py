"""Tests for tool-independent component contracts."""

import unittest

from shared.components import (
    APPROVED_COMPONENTS,
    COMPONENTS,
    OLED_MODULE,
    POWER_SUPPLY,
    SK9822,
    ComponentImplementation,
    ComponentSpec,
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

    def test_selected_display_is_the_ssd1306_module(self) -> None:
        self.assertEqual(OLED_MODULE.manufacturer, "AZ-Delivery")
        self.assertEqual(OLED_MODULE.mpn, "A 1-9")
        self.assertEqual(OLED_MODULE.require_body_mm(), (27.0, 27.0, 4.1))

    def test_invalid_component_envelopes_fail_at_definition_time(self) -> None:
        with self.assertRaisesRegex(ValueError, "body dimensions must be positive"):
            ComponentSpec("X", "invalid", "pkg", "maker", "mpn", (1.0, 0.0, 1.0))

    def test_required_body_dimensions_fail_clearly_when_absent(self) -> None:
        self.assertEqual(SK9822.require_body_mm(), (5.4, 5.0, 1.57))
        with self.assertRaisesRegex(ValueError, "POWER_SUPPLY has no body dimensions"):
            POWER_SUPPLY.require_body_mm()

    def test_domain_implementation_must_build(self) -> None:
        with self.assertRaises(TypeError):
            ComponentImplementation(SK9822)


if __name__ == "__main__":
    unittest.main()
