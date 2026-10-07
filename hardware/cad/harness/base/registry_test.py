"""Registry checks must reject collisions before Blender builds a scene."""

import unittest

from cad.components.printable.board_case import BoardCase

from .component import Component
from .registry import ModelRegistry


class RegistryTest(unittest.TestCase):
    def test_duplicate_reference_is_rejected_without_replacing_the_part(self) -> None:
        model = ModelRegistry()
        original = model.add(BoardCase())
        with self.assertRaisesRegex(ValueError, "duplicate"):
            model.add(BoardCase())
        self.assertEqual(model.components(), (original,))

    def test_two_meshes_cannot_use_the_same_name(self) -> None:
        model = ModelRegistry()
        model.add(BoardCase())

        class Collision(Component):
            @property
            def object_names(self) -> tuple[str, ...]:
                return ("Printable_Board_Case",)

        with self.assertRaisesRegex(ValueError, "unique"):
            model.add(Collision("OTHER"))

    def test_empty_model_cannot_generate(self) -> None:
        with self.assertRaisesRegex(ValueError, "components"):
            ModelRegistry().validate()
