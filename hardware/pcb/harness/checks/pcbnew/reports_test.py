"""A routed-board gate must reject both DRC errors and incomplete copper."""

import json
import tempfile
import unittest
from pathlib import Path

from .reports import check_routed_copper


class CopperReportTest(unittest.TestCase):
    def test_rejects_clearance_errors_and_airwires(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "drc.json"
            for failure in ("violations", "unconnected_items"):
                with self.subTest(failure=failure):
                    report: dict[str, list[str]] = {
                        "violations": [],
                        "unconnected_items": [],
                    }
                    report[failure] = ["finding"]
                    path.write_text(json.dumps(report))
                    with self.assertRaisesRegex(ValueError, failure):
                        check_routed_copper(path)
            path.write_text(json.dumps({"violations": [], "unconnected_items": []}))
            check_routed_copper(path)
