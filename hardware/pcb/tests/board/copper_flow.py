"""Maximum current a net's routed copper can pass between two places.

Each track (split wherever another track ends on it) is an undirected edge whose
capacity is its own ampacity; parallel branches therefore add, and a series
bottleneck limits the whole path. Pads join the endpoints inside their bounding box;
sinks may be pads or vias (each via capped by its barrel's ampacity).
"""

from __future__ import annotations

import math
from collections import defaultdict, deque
from collections.abc import Callable, Sequence
from itertools import pairwise

import pcbnew

Node = tuple[int, int] | str


def _on(point: pcbnew.VECTOR2I, a: pcbnew.VECTOR2I, b: pcbnew.VECTOR2I) -> float | None:
    """Fraction along a-b where `point` lies (within 1 um), else None."""
    dx, dy = b.x - a.x, b.y - a.y
    length = dx * dx + dy * dy
    if length == 0:
        return None
    t = ((point.x - a.x) * dx + (point.y - a.y) * dy) / length
    if not 0.0 < t < 1.0:
        return None
    if math.hypot(a.x + t * dx - point.x, a.y + t * dy - point.y) > 1000:
        return None
    return t


def _key(point: pcbnew.VECTOR2I) -> tuple[int, int]:
    """Snap a point to a 1 um grid so track ends that meet compare equal."""
    return (round(point.x / 1000), round(point.y / 1000))


def max_flow(
    board: pcbnew.BOARD,
    net: str,
    sources: Sequence[pcbnew.PAD],
    sinks: Sequence[pcbnew.PAD | pcbnew.PCB_VIA],
    track_amps: Callable[[float], float],
    via_amps: float,
) -> float:
    """Amps from `sources` to `sinks` over the net's tracks (Edmonds-Karp)."""
    tracks = [
        t
        for t in board.GetTracks()
        if t.GetNetname() == net and not isinstance(t, pcbnew.PCB_VIA)
    ]
    points = [e for t in tracks for e in (t.GetStart(), t.GetEnd())]
    # Vias sitting along a track split it, so each is reached where it stands.
    points += [s.GetPosition() for s in sinks if isinstance(s, pcbnew.PCB_VIA)]
    capacity: dict[Node, dict[Node, float]] = defaultdict(lambda: defaultdict(float))
    for track in tracks:
        a, b = track.GetStart(), track.GetEnd()
        cuts = sorted({t for p in points if (t := _on(p, a, b)) is not None})
        stops = [
            a,
            *(
                pcbnew.VECTOR2I(
                    round(a.x + t * (b.x - a.x)), round(a.y + t * (b.y - a.y))
                )
                for t in cuts
            ),
            b,
        ]
        amps = track_amps(pcbnew.ToMM(track.GetWidth()))
        for start, end in pairwise(stops):
            u, v = _key(start), _key(end)
            capacity[u][v] += amps
            capacity[v][u] += amps
