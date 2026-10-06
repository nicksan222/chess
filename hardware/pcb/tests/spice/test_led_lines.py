"""LED clock/data edges on the routed links as transmission lines (S5).

The first links run from the AHCT125 (Thevenin from its SCLS264R VOH/VOL slopes)
to U6, the data link through R9; every LED-to-LED link runs from an SK9822 output
inside the assumed drive range. At the 4.5 V part floor and the 5.25 V supply
maximum, with the fastest and slowest edge, each receiver stays inside SK9822 §7
(VIN -0.3..VDD+0.3) and crosses its threshold once (`led_lines.edge`); U6 also
stays at or below 5.5 V (lead's S5 bound; its -0.5 V bound is looser than §7).
"""

from __future__ import annotations

import unittest
from collections.abc import Callable

from spice import datasheets
from spice.led_lines import Drive, Link, board_links, edge, setup_margin_ns
from spice.plane_mesh import routed_board
from spice.support import board_circuits, run_circuit

RAILS = (datasheets.AHCT125_VCC.low, datasheets.PSU_VOLTS.high)


def _slope(points: tuple[tuple[float, float], tuple[float, float]]) -> float:
    """Output resistance (ohms) from two datasheet (current, voltage) points: |dV| / dI."""
    (i_small, v_small), (i_large, v_large) = points
    return abs(v_small - v_large) / (i_large - i_small)


def buffer_drives(rising: bool) -> tuple[Drive, ...]:
    """AHCT125 output drive corners for a rising or falling edge: the datasheet VOH/VOL slope at the fast and slow edge times."""
    points = datasheets.AHCT125_VOH_POINTS if rising else datasheets.AHCT125_VOL_POINTS
    return tuple(
        Drive(_slope(points), ns)
        for ns in (datasheets.LED_EDGE_NS.low, datasheets.LED_EDGE_NS.high)
    )


def led_drives(_rising: bool) -> tuple[Drive, ...]:
    """SK9822 output drive corners (the assumed 25-100 ohm output at the fast and slow edge times); the same for both edge directions."""
    return (
        Drive(datasheets.SK9822_OUTPUT_OHMS.low, datasheets.LED_EDGE_NS.low),
        Drive(datasheets.SK9822_OUTPUT_OHMS.high, datasheets.LED_EDGE_NS.high),
    )


class LedLineSpiceTest(unittest.TestCase):
    """LED line edges on the routed board; the links are built once from its copper."""

    links: list[Link]

    @classmethod
    def setUpClass(cls) -> None:
        """Extract every driver-to-receiver link from the routed board once for all tests."""
        cls.links = board_links(routed_board(), board_circuits())

    def run_corners(
        self,
        links: list[Link],
        drives_for: Callable[[bool], tuple[Drive, ...]],
        cap: float | None = None,
    ) -> None:
        """Simulate each link at every supply rail and edge direction with each drive corner, `cap` optionally overriding the receiver capacitance."""
        for link in links:
            for vcc in RAILS:
                for rising in (True, False):
                    for drive in drives_for(rising):
                        with self.subTest(
                            link=link.nets[0], vcc=vcc, rising=rising, drive=drive
                        ):
                            level = "rise" if rising else "fall"
                            name = f"test_led_{link.tag}_{level}_{vcc:g}_{drive.rise_ns:g}.py"
                            margin = datasheets.SK9822_INPUT_ABSOLUTE_MARGIN
                            peak = None if cap is None else min(cap, vcc + margin)
                            circuit = edge(
                                link, drive, vcc=vcc, rising=rising, peak_max=peak
                            )
                            run_circuit(name, circuit)

    def test_buffer_edges_reach_the_first_led_cleanly(self) -> None:
        first = [link for link in self.links if link.driver_part == "AHCT125"]
        self.assertEqual(
            sorted(link.nets[0] for link in first), ["LED_CLK_5V", "LED_DATA_5V"]
        )
        self.run_corners(first, buffer_drives, cap=5.5)

    def test_the_left_turn_data_link_needs_its_series_termination(self) -> None:
        # Mutation in place: R10 shorted (0.1 Ohm) on LED_D16 (In4, about 56 Ohm);
        # the strongest assumed SK9822 output (25 Ohm, 1 ns) must then undershoot
        # past -0.3 V. (Since S6, In6 is a plane, so R9's B.Cu run is referenced at
        # about 33 Ohm and the first link stays clean even without R9; R9 is kept
        # as margin.)
        data = next(link for link in self.links if link.nets[0] == "LED_D16")
        shorted = Link(
            data.tag, data.driver, data.driver_part, data.receiver, data.nets
        )
        shorted.pads = data.pads
        shorted.rows = [
            f"{row.rsplit(' ', 1)[0]} 0.1" if row.startswith("Rser_") else row
            for row in data.rows
        ]
        self.assertNotEqual(shorted.rows, data.rows)
        circuit = edge(shorted, led_drives(False)[0], vcc=RAILS[1], rising=False)
        with self.assertRaises(AssertionError):
            run_circuit("test_led_d16_unterminated.py", circuit)

    def test_led_to_led_edges_stay_clean(self) -> None:
        unique: dict[tuple[str, ...], Link] = {}
        for link in self.links:
            if link.driver_part == "SK9822":
                unique.setdefault(link.signature(), link)
        self.assertEqual(
            sum(link.driver_part == "SK9822" for link in self.links), 2 * 63
        )
        plain = [link for link in unique.values() if len(link.nets) == 1]
        terminated = [link for link in unique.values() if len(link.nets) == 2]
        # R10-R12 (left rank-turn data, lead S5): also within the lead's 5.5 V cap.
        self.assertEqual(
            sum(
                link.driver_part == "SK9822" and len(link.nets) == 2
                for link in self.links
            ),
            3,
        )
        self.run_corners(plain, led_drives)
        self.run_corners(terminated, led_drives, cap=5.5)


class LedSetupSpiceTest(unittest.TestCase):
    """Reviewer m2: at the 10 MHz contract clock every LED pair's data settles
    TSETUP before its clock edge, with the slowest data driver against the
    fastest clock driver."""

    def test_every_link_pair_meets_setup_at_the_contract_clock(self) -> None:
        links = board_links(routed_board(), board_circuits())
        pairs: dict[tuple[str, str], dict[str, Link]] = {}
        for link in links:
            kind = "clock" if link.receiver[1] == "2" else "data"
            pairs.setdefault((link.driver[0], link.receiver[0]), {})[kind] = link
        self.assertEqual(len(pairs), 64)
        seen: set[tuple[tuple[str, ...], tuple[str, ...]]] = set()
        worst = (float("inf"), "")
        for pair in pairs.values():
            data, clock = pair["data"], pair["clock"]
            key = (data.signature(), clock.signature())
            if key in seen:
                continue
            seen.add(key)
            for vcc in RAILS:
                if data.driver_part == "AHCT125":
                    fast = buffer_drives(True)[0]
                else:
                    fast = led_drives(True)[0]
                clock_edge = edge(clock, fast, vcc=vcc, rising=True)
                arrival = run_circuit(
                    f"test_led_setup_{clock.tag}_{vcc:g}.py", clock_edge
                )["result_arrival"]
                for data_rising in (True, False):
                    slow = (
                        buffer_drives(data_rising)[1]
                        if data.driver_part == "AHCT125"
                        else led_drives(data_rising)[1]
                    )
                    settle = run_circuit(
                        f"test_led_setup_{data.tag}_{vcc:g}_{int(data_rising)}.py",
                        edge(data, slow, vcc=vcc, rising=data_rising),
                    )["result_settle"]
                    margin = setup_margin_ns(settle, arrival)
                    worst = min(worst, (margin, data.nets[0]))
                    with self.subTest(link=data.nets[0], vcc=vcc, rising=data_rising):
                        self.assertGreaterEqual(margin, 0.0)
        self.assertGreater(worst[0], 0.0, worst)
