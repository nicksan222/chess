"""Generation must execute pytest functions, including parameterized cases."""

import json
import tempfile
import unittest
from pathlib import Path
from typing import cast

from .suite import run_suite


class SuiteTest(unittest.TestCase):
    def test_runs_plain_and_parameterized_pytest_cases(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tests = root / "tests"
            tests.mkdir()
            (tests / "example_test.py").write_text(
                'import pytest\n@pytest.mark.parametrize("value", [1, 2])\n'
                "def test_value(value):\n    assert value > 0\n"
                "def test_plain():\n    assert True\n"
            )
            result = run_suite(tests, root / "report")
            self.assertEqual(result["passed"], 3)
            self.assertIs(result["complete"], True)

    def test_failure_is_recorded_and_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            tests = root / "tests"
            tests.mkdir()
            (tests / "example_test.py").write_text(
                "def test_bad():\n    assert False\n"
            )
            with self.assertRaisesRegex(ValueError, "electrical tests failed"):
                run_suite(tests, root / "report")
            result = cast(
                dict[str, object],
                json.loads((root / "report/results.json").read_text()),
            )
            self.assertFalse(result["complete"])
            self.assertEqual(result["failed"], 1)

    def test_skip_and_empty_suite_are_incomplete(self) -> None:
        for content in (
            'import pytest\ndef test_skip():\n    pytest.skip("missing input")\n',
            "",
        ):
            with (
                self.subTest(content=content),
                tempfile.TemporaryDirectory() as temporary,
            ):
                root = Path(temporary)
                tests = root / "tests"
                tests.mkdir()
                (tests / "example_test.py").write_text(content)
                if content:
                    self.assertIs(run_suite(tests, root / "report")["complete"], False)
                else:
                    with self.assertRaises(ValueError):
                        run_suite(tests, root / "report")
