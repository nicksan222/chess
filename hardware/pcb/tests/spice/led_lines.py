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


def _add_net(link: Link, board: pcbnew.BOARD, net: str) -> None:
    """Add every segment and via of `net` to the link: lines per segment, via capacitance,
    and merged nodes where copper touches.
    """
    segments: list[tuple[str, float, Point, Point]] = []
    vias: list[Point] = []
    for track in board.GetTracks():
        if track.GetNetname() != net:
            continue
        if isinstance(track, pcbnew.PCB_VIA):
            vias.append(_point(track.GetPosition()))
            continue
        layer = board.GetLayerName(track.GetLayer())
        width = pcbnew.ToMM(track.GetWidth())
        segments.append(
            (layer, width, _point(track.GetStart()), _point(track.GetEnd()))
        )
    points = {p for _, _, a, b in segments for p in (a, b)} | set(vias)
    # Router output can overlap (a track retraced); each copper piece counts once.
    pieces: dict[tuple[str, Point, Point], Line] = {}
    for layer, width, start, end in segments:
        cuts = sorted(
            (t, p) for p in points if (t := _interior(start, end, p)) is not None
        )
        stops = [start, *(p for _, p in cuts), end]
        for a, b in pairwise(stops):
            if a != b:
                low, high = sorted((a, b))
                pieces.setdefault((layer, low, high), line(layer, width))
    lumped: list[tuple[Point, float]] = []
    lines: list[tuple[Point, Point, Line, float]] = []
    for (_layer, a, b), properties in pieces.items():
        mm = pcbnew.ToMM(round(math.hypot(b[0] - a[0], b[1] - a[1])))
        if mm * properties.delay_ns_per_mm < LUMPED_NS:
            link.merge(a, b)
            lumped.append((a, mm * properties.farads_per_mm))
        else:
            lines.append((a, b, properties, mm))
    for footprint in board.GetFootprints():
        for pad in footprint.Pads():
            if pad.GetNetname() != net:
                continue
            inside = sorted(p for p in points if pad.HitTest(pcbnew.VECTOR2I(*p)))
            key = (footprint.GetReference(), pad.GetNumber())
            if not inside:
                raise ValueError(f"{net}: no routed copper reaches {key}")
            for other in inside[1:]:
                link.merge(inside[0], other)
            link.pads[key] = inside[0]
    for a, b, properties, mm in lines:
        name = f"{link.tag}_{len(link.rows)}"
        if link.root(a) == link.root(b):
            link.rows.append(
                f"C{name} {link.node(a)} 0 {mm * properties.farads_per_mm}"
            )
            continue
        delay = mm * properties.delay_ns_per_mm
        link.rows.append(
            f"T{name} {link.node(a)} 0 {link.node(b)} 0 "
            f"Z0={properties.impedance} TD={delay}n"
        )
    for point, farads in [*lumped, *((via, via_farads()) for via in vias)]:
        link.rows.append(f"C{link.tag}_{len(link.rows)} {link.node(point)} 0 {farads}")


def board_links(board: pcbnew.BOARD, harness: BoardHarness) -> list[Link]:
    """Every SK9822 clock/data input with its driver, through any series resistor."""
    pads_by_net: dict[str, list[tuple[str, str, str]]] = {}
    for footprint in board.GetFootprints():
        has_key = footprint.HasFieldByName("PartKey")
        part = footprint.GetFieldText("PartKey") if has_key else ""
        for pad in footprint.Pads():
            pads_by_net.setdefault(pad.GetNetname(), []).append(
                (footprint.GetReference(), str(pad.GetNumber()), part)
            )
    # S6d: a resistor with one terminal on GND is a pull-down (shunt), not a series
    # element of the link.
    shunts = {r for r, _, p in pads_by_net.get("GND", ()) if p.startswith("RES_")}
    links: list[Link] = []
    for net, pads in pads_by_net.items():
        receivers = [
            (r, n) for r, n, part in pads if part == "SK9822" and n in INPUT_PINS
        ]
        if not receivers:
            continue
        nets = [net]
        drivers = [(r, n, p) for r, n, p in pads if n in OUTPUT_PINS.get(p, ())]
        if not drivers:
            series = [r for r, _, p in pads if p.startswith("RES_") and r not in shunts]
            if len(series) != 1:
                raise ValueError(f"{net}: no driver and no single series resistor")
            other = next(
                n
                for n, ps in pads_by_net.items()
                if n != net and any(r == series[0] for r, _, _ in ps)
            )
            nets.append(other)
            drivers = [
                (r, n, p)
                for r, n, p in pads_by_net[other]
                if n in OUTPUT_PINS.get(p, ())
            ]
        if len(receivers) != 1 or len(drivers) != 1:
            raise ValueError(f"{net}: expected one driver and one SK9822 input")
        reference, number, part = drivers[0]
        tag = "l" + "".join(c if c.isalnum() else "_" for c in net).lower()
        link = Link(tag, (reference, number), part, receivers[0], tuple(nets))
        for name in nets:
            _add_net(link, board, name)
        for name in nets:
            for reference, number, part in pads_by_net[name]:
                if not part.startswith("RES_"):
                    continue
                nominal, tolerance = harness.resistor_ohms(reference)
                if reference in shunts:
                    node = link.node(link.pads[(reference, number)])
                    link.rows.append(f"Rpd_{reference} {node} 0 {nominal}")
                elif name == net:
                    ends = [
                        link.node(link.pads[(reference, pin)]) for pin in ("1", "2")
                    ]
                    ohms = nominal * (1 - tolerance)  # low end: least damping
                    link.rows.append(f"Rser_{link.tag} {ends[0]} {ends[1]} {ohms}")
        links.append(link)
    return links


@dataclass(frozen=True)
class Drive:
    """Driver corner: Thevenin resistance and 0-100 % ramp time."""

    ohms: float
    rise_ns: float


def edge(
    link: Link,
    drive: Drive,
    *,
    vcc: float,
    rising: bool,
    peak_max: float | None = None,
) -> SpiceCircuit:
    """One driver edge on one link (links run alone: many unrelated line delays in
    one deck multiply ngspice's breakpoints), with its limits as expectations.

    peak <= VDD + 0.3 V (or `peak_max`) and trough >= -0.3 V (SK9822 §7 VIN);
    `hold` stays past the far threshold; `settle` (ns from the edge start until the
    last crossing of 90 % / 10 % of VDD) is at most half a §8 clock phase.
    """
    t = link.tag
    start, end = (0.0, vcc) if rising else (vcc, 0.0)
    receiver = link.node(link.pads[link.receiver])
    circuit = SpiceCircuit(f"LED link {link.nets[0]}, {drive}, {vcc:g} V")
    circuit.rows.extend(
        (
            *link.rows,
            f"V{t} {t}_src 0 PULSE({start} {end} {EDGE_START_NS}n {drive.rise_ns}n 1n 100n 200n)",
            f"Rdrv_{t} {t}_src {link.node(link.pads[link.driver])} {drive.ohms}",
            f"Crx_{t} {receiver} 0 {datasheets.SK9822_INPUT_FARADS}",
            f".tran 10p {END_NS}n",
        )
    )
    fraction = (
        datasheets.SK9822_VIH_FRACTION if rising else datasheets.SK9822_VIL_FRACTION
    )
    far = fraction * vcc
    direction, extreme = ("RISE", "MIN") if rising else ("FALL", "MAX")
    circuit.controls.extend(
        (
            f"meas tran cross WHEN v({receiver})={far} {direction}=1",
            f"meas tran result_peak MAX v({receiver})",
            f"meas tran result_trough MIN v({receiver})",
            f"meas tran result_hold {extreme} v({receiver}) FROM=$&cross",
            f"meas tran last WHEN v({receiver})={(0.9 if rising else 0.1) * vcc} CROSS=LAST",
            f"let result_settle = (last - {EDGE_START_NS}n) * 1e9",
            f"let result_arrival = (cross - {EDGE_START_NS}n) * 1e9",
            "print result_settle",
            "print result_arrival",
        )
    )
    circuit.expect("settle", 0.0, SETTLE_NS)
    margin = datasheets.SK9822_INPUT_ABSOLUTE_MARGIN
    circuit.expect("peak", 0.0, vcc + margin if peak_max is None else peak_max)
    circuit.expect("trough", -margin, vcc)
    # 5 mV numerical allowance: `hold` starts exactly at the crossing.
    if rising:
        circuit.expect("hold", far - 0.005, vcc + margin)
    else:
        circuit.expect("hold", -margin, far + 0.005)
    return circuit


def setup_margin_ns(data_settle_ns: float, clock_arrival_ns: float) -> float:
    """Data-to-clock setup at the receiver at the contract clock (reviewer m2).

    Data changes at the driver's clock-low edge; the next rising clock leaves the
    driver half a period later. The receiver needs the data settled (last 10/90 %
    crossing, `edge` result `settle`) TSETUP before the clock crosses 0.7 x VDD
    (`edge` result `arrival`). Links are simulated separately (their delays in one
    deck multiply ngspice breakpoints).
    """
    return (
        datasheets.SK9822_CLOCK_PHASE_NS
        + clock_arrival_ns
        - data_settle_ns
        - datasheets.SK9822_SETUP_NS
    )
