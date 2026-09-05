"""Native identity stability without a frozen component ledger."""

import unittest

from pcb.definition import native
from shared.electronics import HallSensorComponent


class NativeIdentityTest(unittest.TestCase):
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
