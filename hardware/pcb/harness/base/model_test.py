"""3D declarations reject invalid solids and preserve product dimensions."""

import unittest

from .model import Model3D, Solid3D


class ModelTest(unittest.TestCase):
    def test_body_envelope_sits_on_the_component_mounting_face(self) -> None:
        model = Model3D.envelope((6, 4, 2))
        self.assertEqual(model.solids[0].size_mm, (6, 4, 2))
        self.assertEqual(model.solids[0].center_mm, (0, 0, 1))
        self.assertEqual(model.fidelity, "dimension-based envelope")

    def test_empty_model_and_invalid_dimensions_are_rejected(self) -> None:
        with self.assertRaises(ValueError):
            Model3D(())
        with self.assertRaises(ValueError):
            Solid3D("body", (1, 0, 1))
        with self.assertRaises(ValueError):
            Solid3D("body", (1, 1, float("nan")))

    def test_duplicate_solid_names_are_rejected(self) -> None:
        body = Solid3D("body", (1, 1, 1))
        with self.assertRaises(ValueError):
            Model3D((body, body))
