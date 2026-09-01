"""Tests for tool-independent component contracts."""

import unittest

from shared.components import (
    APPROVED_COMPONENTS,
    COMPONENTS,
    POWER_SUPPLY,
    SK9822,
    ComponentImplementation,
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

    def test_required_body_dimensions_fail_clearly_when_absent(self) -> None:
        self.assertEqual(SK9822.require_body_mm(), (5.4, 5.0, 1.57))
        with self.assertRaisesRegex(ValueError, "POWER_SUPPLY has no body dimensions"):
            POWER_SUPPLY.require_body_mm()

    def test_domain_implementation_must_build(self) -> None:
        with self.assertRaises(TypeError):
            ComponentImplementation(SK9822)


if __name__ == "__main__":
    unittest.main()
