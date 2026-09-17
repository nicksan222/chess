"""Native identity stability without a frozen component ledger."""

import unittest

from pcb.definition import native
from pcb.definition.parts import catalog
from shared.components import COMPONENTS
from shared.electronics import HallSensorComponent


class NativeIdentityTest(unittest.TestCase):
    def test_registry_owns_every_native_product_once(self):
        self.assertEqual(set(catalog.PCB_PARTS), set(catalog.MODELS))
        self.assertEqual(set(catalog.PCB_PARTS), set(catalog.TEMPLATES))
        for key, part in catalog.PCB_PARTS.items():
            with self.subTest(part=key):
                self.assertIs(part.spec, COMPONENTS[key])
                self.assertEqual(
                    part.template.GetFieldText("Package"), part.spec.package
                )
                self.assertTrue(part.new_model("X1").supports_part_key(key))

    def test_registry_rejects_a_model_for_the_wrong_product(self):
        with self.assertRaisesRegex(ValueError, "model does not support product"):
            catalog.PcbPart(
                COMPONENTS["CAP_100N"],
                HallSensorComponent,
                catalog.CAPACITOR_0603_FOOTPRINT,
                "C",
                "100nF",
                "test",
            )

    def test_unrelated_insertion_and_reordering_keep_component_and_pad_ids(self):
        def identities(references):
            board = native.new_board()
            for reference in references:
                native.place(
                    board,
                    HallSensorComponent(reference),
                    part_key="HALL_SENSOR",
                    at=(0.0, 0.0),
                    assembly="test",
                    library="HALL",
                    value="DRV5032FC",
                    description="Identity test",
                )
            mapping = native.stable_uuid_map(board)
            return {
                f.GetReference(): (
                    mapping[f.m_Uuid.AsString()],
                    sorted(
                        (p.GetNumber(), mapping[p.m_Uuid.AsString()]) for p in f.Pads()
                    ),
                )
                for f in board.GetFootprints()
            }

        baseline = identities(("HS1", "HS2"))
        inserted = identities(("HS3", "HS2", "HS1"))
        self.assertEqual(baseline, {ref: inserted[ref] for ref in baseline})
