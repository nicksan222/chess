"""Does the copper actually implement the design contract?

This is the gate. An unrouted board still produces perfectly valid Gerber files,
and a fab will accept them and ship the boards: valid is not the same as
connected. So the fabrication package is only written when every connection the
design contract declares is realised in copper, and until then this module says exactly
what is missing.

It works by union-find over pads, joining them the way copper joins them:

- a trace joins any pads and vias at its two ends;
- a via joins the two layers, so anything reaching it reaches the pour;
- the bottom pour joins every through-hole pad on ground, plus every ground via.

Note the limits, because they matter for how much this check is worth. It reasons
about endpoints, not geometry: it will not notice a trace crossing another net,
and it will not notice two pads that happen to overlap. It answers "is this net
joined up", not "is this board correct".
"""

from __future__ import annotations

from dataclasses import dataclass

from core import nets, sources
from core.layers import Artwork
from core.placement import Placement
from core.routing import pad_positions, surface_mount_pads

TOLERANCE_MM = 0.01


@dataclass(frozen=True)
class NetStatus:
    """One design contract connection, and whether copper realises it."""

    name: str
    pads: tuple[tuple[str, str], ...]
    islands: int

    @property
    def routed(self) -> bool:
        return self.islands <= 1

    @property
    def missing_links(self) -> int:
        return max(0, self.islands - 1)


class _Union:
    def __init__(self) -> None:
        self._parent: dict[object, object] = {}

    def add(self, item: object) -> object:
        self._parent.setdefault(item, item)
        return item

    def find(self, item: object) -> object:
        self.add(item)
        while self._parent[item] != item:
            self._parent[item] = self._parent[self._parent[item]]
            item = self._parent[item]
        return item

    def union(self, a: object, b: object) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self._parent[rb] = ra


def _key(position: tuple[float, float]) -> tuple[int, int]:
    """Snap a coordinate so two things meant to touch compare equal."""
    scale = 1.0 / TOLERANCE_MM
    return (round(position[0] * scale), round(position[1] * scale))


def analyse(placements: list[Placement], artwork: Artwork) -> list[NetStatus]:
    """One status per design contract connection that needs more than one pad."""
    netlist = sources.netlist()
    positions = pad_positions(placements)
    surface = surface_mount_pads(placements)
    pad_net = nets.pad_nets()

    union = _Union()
    # A pad is joined to the point it sits on, so a trace ending there finds it.
    at_point: dict[tuple[int, int], list[tuple[str, str]]] = {}
    for pad, position in positions.items():
        union.union(pad, _key(position))
        at_point.setdefault(_key(position), []).append(pad)

    for trace in artwork.traces:
        union.union(_key(trace.start), _key(trace.end))
    for via in artwork.vias:
        union.add(_key(via.at))

    # The bottom pour is one conductor. Everything on ground that reaches the
    # bottom layer is therefore joined: through-hole pads by their own barrel,
    # and surface-mount pads through the via stitched next to them.
    pour = "bottom-ground-pour"
    union.add(pour)
    for pad, position in positions.items():
        if not nets.is_ground(pad_net.get(pad)):
            continue
        if pad not in surface:
            union.union(pour, _key(position))
    for via in artwork.vias:
        if nets.is_ground(via.net):
            union.union(pour, _key(via.at))

    statuses = []
    for connection in netlist["connections"]:
        pads = tuple(tuple(pad) for pad in connection["pads"])
        if len(pads) < 2:
            # A single pad needs no copper. Every one of these is a deliberate
            # no-connect: unused Pi lines, the expanders' NC and INTB pins, the
            # buffer's spare outputs, and the end-of-chain labels.
            continue
        islands = len({union.find(pad) for pad in pads})
        statuses.append(
            NetStatus(
                name=connection["name"] or f"unnamed:{pads[0][0]}.{pads[0][1]}",
                pads=pads,
                islands=islands,
            )
        )
    statuses.sort(key=lambda status: (status.routed, status.name))
    return statuses


def summary(statuses: list[NetStatus]) -> dict:
    unrouted = [status for status in statuses if not status.routed]
    return {
        "connections": len(statuses),
        "routed": len(statuses) - len(unrouted),
        "unrouted": len(unrouted),
        "missing_links": sum(status.missing_links for status in unrouted),
        "complete": not unrouted,
    }


def report(statuses: list[NetStatus], limit: int = 12) -> str:
    """A human-readable account of what is left to route."""
    counts = summary(statuses)
    lines = [
        f"{counts['routed']}/{counts['connections']} connections routed, "
        f"{counts['missing_links']} links missing",
    ]
    if counts["complete"]:
        lines.append("Every design contract connection is realised in copper.")
        return "\n".join(lines)

    grouped: dict[str, int] = {}
    for status in statuses:
        if status.routed:
            continue
        grouped[_family(status.name)] = grouped.get(_family(status.name), 0) + 1
    lines.append("Outstanding, by group:")
    for family, count in sorted(grouped.items(), key=lambda item: -item[1]):
        lines.append(f"  {count:4d}  {family}")
    lines.append("Examples:")
    for status in [s for s in statuses if not s.routed][:limit]:
        pads = " ".join(f"{reference}.{pin}" for reference, pin in status.pads[:4])
        more = " ..." if len(status.pads) > 4 else ""
        lines.append(f"  {status.name:16s} {status.islands:3d} islands  {pads}{more}")
    return "\n".join(lines)


def _family(name: str) -> str:
    """Bucket net names so the report reads as a work list, not a wall."""
    if name.startswith("SQ_"):
        return "SQ_* reed sense lines"
    if name.startswith("BTN_"):
        return "BTN_* panel buttons"
    if name.startswith("LED_"):
        return "LED_* chain and buffered signals"
    if name.startswith("unnamed:"):
        return "unnamed point-to-point links"
    if name in {"+5V", "+3V3", "GND"}:
        return f"{name} power distribution"
    return "buses and one-off signals"
