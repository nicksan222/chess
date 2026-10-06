"""`release` refuses while any land is unverified or any design value is assumed.

The gate (`build.verification_gate`) must list every open item by name, so a reviewer can
see exactly what stands between the design and fabrication.
"""

import unittest
from types import MappingProxyType
from unittest import mock

from pcb import build
from pcb.definition import verification


class VerificationGateTest(unittest.TestCase):
    """`verification_gate()` refuses with every open item named."""

    def test_every_open_item_is_listed_in_the_refusal(self) -> None:
        with self.assertRaises(RuntimeError) as raised:
            build.verification_gate()
        message = str(raised.exception)
        for key in (*verification.UNVERIFIED, *verification.ASSUMPTIONS):
            with self.subTest(item=key):
                self.assertIn(key, message)

    def test_gate_opens_only_when_nothing_is_open(self) -> None:
        empty: MappingProxyType[str, str] = MappingProxyType({})
        with (
            mock.patch.object(verification, "UNVERIFIED", empty),
            mock.patch.object(verification, "ASSUMPTIONS", empty),
        ):
            self.assertIsNone(build.verification_gate())
        with (
            mock.patch.object(verification, "UNVERIFIED", empty),
            self.assertRaises(RuntimeError),
        ):
            build.verification_gate()


if __name__ == "__main__":
    unittest.main()
