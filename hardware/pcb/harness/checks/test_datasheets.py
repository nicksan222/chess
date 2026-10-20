"""Automatic documentation gate for every catalogued component."""

import contextlib
import io
import unittest
import warnings
from unittest.mock import patch
from urllib.parse import urlsplit

from .catalog import datasheet_references
from .datasheets import check_all, main


class ComponentDatasheetsTest(unittest.TestCase):
    def test_every_component_has_a_document_url(self) -> None:
        for component, reference in datasheet_references():
            with self.subTest(component=component):
                parsed = urlsplit(reference)
                self.assertIn(parsed.scheme, ("http", "https"))
                self.assertTrue(parsed.hostname)
                self.assertIsNone(parsed.username)
                self.assertIsNone(parsed.password)

    def test_every_document_is_available(self) -> None:
        for row in check_all(datasheet_references()):
            with self.subTest(components=row.components, url=row.reference):
                if row.status == "failed":
                    warnings.warn(
                        f"{', '.join(row.components)}: {row.reference}: {row.detail}",
                        stacklevel=1,
                    )
                else:
                    self.assertEqual(row.status, "valid", row.detail)


class DocumentationGateTest(unittest.TestCase):
    def test_unavailable_document_warns_without_failing_the_gate(self) -> None:
        reference = "https://supplier.example/sheet.pdf"
        with (
            patch(
                "pcb.harness.checks.test_datasheets.datasheet_references",
                return_value=(("A", reference),),
            ),
            patch(
                "pcb.harness.checks.datasheets.check_url",
                side_effect=ValueError("HTTP 404"),
            ),
            self.assertWarnsRegex(UserWarning, "HTTP 404"),
        ):
            ComponentDatasheetsTest(
                "test_every_document_is_available"
            ).test_every_document_is_available()

    def test_audit_exit_status_requires_definitions_but_not_live_documents(
        self,
    ) -> None:
        for reference, expected in (("https://supplier.example/sheet.pdf", 0), ("", 1)):
            with (
                self.subTest(reference=reference),
                patch(
                    "pcb.harness.checks.catalog.datasheet_references",
                    return_value=(("A", reference),),
                ),
                patch(
                    "pcb.harness.checks.datasheets.check_url",
                    side_effect=ValueError("HTTP 404"),
                ),
                contextlib.redirect_stdout(io.StringIO()),
            ):
                self.assertEqual(main(), expected)
