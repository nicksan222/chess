"""Tests for shared electronic connection values."""

import json
import unittest

from shared.electronics import Endpoint, Sk9822Pin


class EndpointTest(unittest.TestCase):
    def test_endpoint_preserves_sorted_serialized_connection_shape(self):
        endpoints = [Endpoint("U2", "1"), Endpoint("U1", "2")]

        self.assertEqual(
            [endpoint.reference for endpoint in sorted(endpoints)], ["U1", "U2"]
        )
        self.assertEqual(json.loads(json.dumps(endpoints)), [["U2", "1"], ["U1", "2"]])

    def test_enum_pin_finds_the_serialized_string_endpoint(self):
        serialized = Endpoint("U1", "1")
        typed = Endpoint("U1", Sk9822Pin.DATA_IN)

        self.assertEqual(typed, serialized)
        self.assertEqual(hash(typed), hash(serialized))
        self.assertEqual({serialized: "data in"}[typed], "data in")


if __name__ == "__main__":
    unittest.main()
