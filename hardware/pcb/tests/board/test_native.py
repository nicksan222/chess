"""Native identity stability without a frozen component ledger."""

import unittest

from pcb.definition import native
from pcb.definition.parts import catalog
from shared.components import COMPONENTS
from shared.electronics import HallSensorComponent, HallSensorPin


class NativeIdentityTest(unittest.TestCase):
    def test_registry_owns_every_native_product_once(self):
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
                    catalog.HALL_SENSOR_PART,
                    reference,
                    at=(0.0, 0.0),
                    assembly="test",
                    purpose="Identity test",
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

    def test_duplicate_references_and_pin_ownership_are_rejected(self):
        board = native.new_board()
        sensor = native.place(
            board,
            catalog.HALL_SENSOR_PART,
            "HS1",
            at=(0.0, 0.0),
            assembly="test",
        )
        with self.assertRaisesRegex(ValueError, "duplicate reference"):
            native.place(
                board,
                catalog.HALL_SENSOR_PART,
                "HS1",
                at=(1.0, 0.0),
                assembly="test",
            )
        supply = sensor.pin(HallSensorPin.SUPPLY)
        with self.assertRaisesRegex(ValueError, "repeated pin"):
            native.connect(board, "+3V3", supply, supply)
        native.connect(board, "+3V3", supply)
        with self.assertRaisesRegex(ValueError, "already connected"):
            native.connect(board, "+5V", supply)
