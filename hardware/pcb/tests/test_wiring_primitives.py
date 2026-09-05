"""Exact escapes and bank coordinate conversion retain the reviewed routing geometry."""

import unittest

try:
    from base.kicad.api import pcbnew
except ModuleNotFoundError:  # Host-only unit runs do not install KiCad.
    pcbnew = None

if pcbnew is not None:
    from base.kicad import board as kicad
    from board import definition
    from board.wiring import common, power, sensors
    from shared.dimensions import HALL_BANKS


@unittest.skipUnless(pcbnew is not None, "KiCad pcbnew is not installed")
class WiringPrimitivesTest(unittest.TestCase):
    def setUp(self):
        self.design = definition.load()
        self.layout = kicad.KiCadBoard(self.design)

    def attach(self, reference):
        self.layout.attach(self.design.component(reference))
        return self.layout.native.FindFootprintByReference(reference)

    def test_first_and_last_bank_bounds_use_native_y_down_coordinates(self):
        self.assertEqual(
            sensors._bank_routing_bounds_mm(HALL_BANKS[0]), (41, 301, 199, 379)
        )
        self.assertEqual(
            sensors._bank_routing_bounds_mm(HALL_BANKS[-1]), (201, 61, 359, 139)
        )

    def test_tca9554_power_and_signal_escapes_preserve_all_sixteen_pads(self):
        module = self.attach("U1")
        # Explicit four-row sequence, independent of the shared modulo helper.
        distances = (2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 5)
        for number, distance in enumerate(distances, 1):
            with self.subTest(pin=number):
                pad = module.FindPadByNumber(str(number))
                at = pad.GetPosition()
                expected = pcbnew.VECTOR2I(
                    at.x + pcbnew.FromMM(-distance if number <= 8 else distance), at.y
                )
                self.assertEqual(power._power_escape_position(module, pad), expected)
                self.assertEqual(
                    common.signal_escape(self.layout.native, pad.GetNet(), pad),
                    expected,
                )

    def test_ahct125_keeps_distinct_power_and_signal_escape_distances(self):
        module = self.attach("U5")
        for number, distance in enumerate(
            (2, 3, 4, 5, 2, 3, 4, 5, 2, 3, 4, 5, 2, 3), 1
        ):
            with self.subTest(pin=number):
                pad = module.FindPadByNumber(str(number))
                at = pad.GetPosition()
                direction = -1 if number <= 7 else 1
                self.assertEqual(
                    power._power_escape_position(module, pad),
                    pcbnew.VECTOR2I(at.x + pcbnew.FromMM(direction * 1.2), at.y),
                )
                self.assertEqual(
                    common.signal_escape(self.layout.native, pad.GetNet(), pad),
                    pcbnew.VECTOR2I(at.x + pcbnew.FromMM(direction * distance), at.y),
                )

    def test_pending_hall_routes_preserve_address_port_order_and_endpoints(self):
        for component in self.design.components.values():
            self.layout.attach(component)
        pending = sensors.reserve_square_sensor_breakouts(
            self.layout.native, self.layout.nets, self.layout.pads, self.design
        )
        expected_names = [
            f"SQ_{'ABCDEFGH'[column * 4 + offset]}{row * 2 + rank}"
            for row in range(4)
            for column in range(2)
            for offset, rank in (
                (0, 1),
                (1, 1),
                (0, 2),
                (1, 2),
                (2, 1),
                (3, 1),
                (2, 2),
                (3, 2),
            )
        ]
        self.assertEqual([route.net.GetNetname() for route in pending], expected_names)
        first = pending[0]
        self.assertEqual(first.bounds_mm, (41, 301, 199, 379))
        # SQ_A1 = HS1 output escape and U1 P0 (pin 4) escape.
        hall = self.layout.pads[("HS1", "2")].GetPosition()
        expander = self.layout.pads[("U1", "4")].GetPosition()
        expected = {
            (hall.x - pcbnew.FromMM(3), hall.y),
            (expander.x - pcbnew.FromMM(5), expander.y),
        }
        self.assertEqual(
            {(first.start.x, first.start.y), (first.end.x, first.end.y)}, expected
        )


if __name__ == "__main__":
    unittest.main()
