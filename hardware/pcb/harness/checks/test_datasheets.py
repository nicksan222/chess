"""Automatic documentation gate for every catalogued component."""

import unittest
from urllib.parse import urlsplit

from .catalog import datasheet_references
from .datasheets import check_all


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
                self.assertEqual(row.status, "valid", row.detail)
