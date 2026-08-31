"""Tests for tool-independent component contracts."""

import unittest

from shared.components import COMPONENTS, ComponentImplementation, SK9822


class ComponentsTest(unittest.TestCase):
    def test_component_keys_are_canonical(self):
        self.assertEqual(COMPONENTS[SK9822.key], SK9822)
        self.assertEqual(len(COMPONENTS), len(set(COMPONENTS)))

    def test_domain_implementation_must_build(self):
        with self.assertRaises(TypeError):
            ComponentImplementation(SK9822)


if __name__ == "__main__":
    unittest.main()
