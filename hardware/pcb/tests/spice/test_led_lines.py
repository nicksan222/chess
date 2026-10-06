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
