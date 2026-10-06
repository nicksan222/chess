"""LED clock/data links as lossless transmission lines built from the routed copper.

Every routed segment of a link's nets becomes a lossless line with the layer's
IPC-2141 impedance and delay (`bus_lines.line`), split where another segment or a
via joins it; vias add their plane capacitance; pads join the segment ends they
contain. A series resistor between two nets (R9 on the first data link) joins its
pads. The driver is a ramp behind a resistance, the receiver an SK9822 input
(`datasheets.SK9822_INPUT_FARADS`, verification ASSUMPTION "SK9822 input").

Each edge records the receiver's peak/trough (`result_<tag>_peak` / `_trough`) and
`_hold`: after the receiver first crosses the far threshold (0.7 / 0.3 x VDD) it must
stay past it, so the edge is monotonic through the threshold band and clocks once.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from itertools import pairwise

import pcbnew

from shared.electronics import Ahct125Pin, Sk9822Pin
from spice import datasheets
from spice.board_harness import BoardHarness
from spice.bus_lines import Line, line, via_farads
from spice.circuit import SpiceCircuit

SNAP_NM = 1000
LUMPED_NS = 0.05  # Pieces under 1/20 of the fastest 1 ns edge are a lumped C.
END_NS = 60.0
EDGE_START_NS = 1.0
SETTLE_NS = datasheets.SK9822_CLOCK_PHASE_NS / 2
INPUT_PINS = {str(Sk9822Pin.DATA_IN), str(Sk9822Pin.CLOCK_IN)}
OUTPUT_PINS = {
    "AHCT125": {str(Ahct125Pin.BUFFER_1_OUTPUT), str(Ahct125Pin.BUFFER_2_OUTPUT)},
    "SK9822": {str(Sk9822Pin.DATA_OUT), str(Sk9822Pin.CLOCK_OUT)},
}

Point = tuple[int, int]
Pad = tuple[str, str]


def _point(vector: pcbnew.VECTOR2I) -> Point:
    """Snap a native point to a 1 um grid so coincident track ends and pads compare equal."""
    return (round(vector.x / SNAP_NM) * SNAP_NM, round(vector.y / SNAP_NM) * SNAP_NM)


def _interior(start: Point, end: Point, point: Point) -> float | None:
    """Fraction along start->end if `point` lies inside the segment, else None."""
    dx, dy = end[0] - start[0], end[1] - start[1]
    length2 = dx * dx + dy * dy
    if length2 == 0 or point in (start, end):
        return None
    t = ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy) / length2
    if not 0 < t < 1:
        return None
    off = abs((point[0] - start[0]) * dy - (point[1] - start[1]) * dx) / math.sqrt(
        length2
    )
    return t if off <= SNAP_NM else None


@dataclass
class Link:
    """One routed driver -> receiver link (possibly through a series resistor)."""

    tag: str
    driver: Pad
    driver_part: str
    receiver: Pad
    nets: tuple[str, ...]
    rows: list[str] = field(default_factory=list)
    pads: dict[Pad, Point] = field(default_factory=dict)
    nodes: dict[Point, str] = field(default_factory=dict)
    merged: dict[Point, Point] = field(default_factory=dict)

    def signature(self) -> tuple[str, ...]:
        """Geometry identity: links with equal copper simulate identically."""
        ends = (self.node(self.pads[self.driver]), self.node(self.pads[self.receiver]))
        rows = (*self.rows, *ends)
        return (self.driver_part, *(row.replace(self.tag, "x") for row in rows))

    def root(self, point: Point) -> Point:
        """Follow merged nodes to the representative point of an electrical node."""
        while point in self.merged:
            point = self.merged[point]
        return point

    def merge(self, first: Point, second: Point) -> None:
        """One electrical node (lumped copper or a pad): no stiff milliohm links."""
        a, b = self.root(first), self.root(second)
        if a != b:
            self.merged[max(a, b)] = min(a, b)

    def node(self, point: Point) -> str:
        """Name of the SPICE node for a point, allocating a new one on first use."""
        point = self.root(point)
        if point not in self.nodes:
            self.nodes[point] = f"{self.tag}_{len(self.nodes)}"
        return self.nodes[point]
