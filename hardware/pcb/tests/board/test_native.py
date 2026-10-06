"""Native identity stability without a frozen component ledger.

Role: checks the authoring layer in `native.py` and the part registry: that
identities (UUIDs) are derived from meaning rather than insertion order, that the
registry binds each approved product to a matching footprint, and that the
guard rails (duplicate references, repeated or re-assigned pins, missing
assemblies) fail loudly. Uses throwaway in-memory boards, never the generated files.
"""

import unittest

from pcb.definition import native, validation
from pcb.definition.parts import catalog
from pcb.definition.parts.capacitors import CAPACITOR_0603_FOOTPRINT
from pcb.definition.parts.part import DrawingView, PcbPart
from shared.components import COMPONENTS
from shared.electronics import HallSensorComponent, HallSensorPin


class NativeIdentityTest(unittest.TestCase):
    def test_missing_assembly_reports_its_owner(self):
        # An empty board must fail validation naming the first missing assembly
        # (power, expecting 9 parts), so a failure points at its owner.
        with self.assertRaisesRegex(
            ValueError, "power: expected 20 components, found 0"
        ):
            validation.validate(native.new_board())

    def test_registry_owns_every_native_product_once(self):
        # Each registered part must bind the shared catalog's own spec object, use a
        # footprint whose package field matches the spec, and offer a model that
        # accepts that product key.
        for key, part in catalog.PCB_PARTS.items():
            with self.subTest(part=key):
                self.assertIs(part.spec, COMPONENTS[key])
                self.assertEqual(
                    part.template.GetFieldText("Package"), part.spec.package
                )
                self.assertTrue(part.new_model("X1").supports_part_key(key))

    def test_registry_rejects_a_model_for_the_wrong_product(self):
        # A 100 nF capacitor bound to the Hall-sensor pin model is a wiring mistake
        # waiting to happen; constructing the binding must refuse it.
        with self.assertRaisesRegex(ValueError, "model does not support product"):
            PcbPart(
                COMPONENTS["CAP_100N"],
                HallSensorComponent,
                CAPACITOR_0603_FOOTPRINT,
                "C",
                "100nF",
                "test",
                DrawingView.MOUNTING_SIDE,
            )

    def test_unrelated_insertion_and_reordering_keep_component_and_pad_ids(self):
        # Build two boards with overlapping parts added in different order (and one
        # extra); the shared parts must get identical footprint and pad UUIDs. This
        # is what keeps diffs of the generated board free of identity churn.
        def identities(
            references: tuple[str, ...],
        ) -> dict[str, tuple[str, list[tuple[str, str]]]]:
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
        # Reusing a reference, listing a pin twice in one connection, and assigning
        # an already-connected pin to another net must each raise.
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
