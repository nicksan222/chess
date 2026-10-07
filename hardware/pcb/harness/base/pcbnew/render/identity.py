"""Replace KiCad's random board-item UUIDs with stable semantic identities.

The native SDK assigns random IDs while objects are created. Those IDs make
unchanged generated boards appear different in code review. This adapter maps
each native item to a UUID derived from what it represents, then substitutes
those IDs in the serialized board. It does not alter geometry or connectivity.
"""

from __future__ import annotations

import re
import uuid
from collections import Counter
from pathlib import Path

import pcbnew

from pcb.harness.base.pcbnew.render.order import order_footprints

_NAMESPACE = uuid.UUID("8e953e42-4f68-47ae-9c71-b0d9b6829701")
_UUID_PATTERN = re.compile(r'\(uuid "([0-9a-fA-F-]+)"\)')


def stable_uuid_map(board: pcbnew.BOARD) -> dict[str, str]:
    """Map native random IDs to stable IDs for the same semantic board items.

    Component references and pad numbers provide durable names. Copper paths
    use net, layer, endpoints and size; exact duplicates receive a local
    occurrence number. Adding an unrelated item therefore leaves existing
    references, pads and unlike paths unchanged.
    """
    identities: dict[str, str] = {}
    occurrences: Counter[str] = Counter()

    def add(item: pcbnew.BOARD_ITEM, key: str) -> None:
        index = occurrences[key]
        occurrences[key] += 1
        identities[item.m_Uuid.AsString()] = str(
            uuid.uuid5(_NAMESPACE, f"{key}:{index}")
        )

    def segment_key(shape: pcbnew.PCB_SHAPE, origin: pcbnew.VECTOR2I) -> str:
        ends = sorted(
            (point.x - origin.x, point.y - origin.y)
            for point in (shape.GetStart(), shape.GetEnd())
        )
        return f"shape:{shape.GetLayer()}:{shape.GetShape()}:{ends}:{shape.GetWidth()}"

    for footprint in board.GetFootprints():
        key = f"footprint:{footprint.GetReference()}"
        add(footprint, key)
        for field in footprint.GetFields():
            add(field, f"{key}/field:{field.GetName()}")
        for pad in footprint.Pads():
            add(pad, f"{key}/pad:{pad.GetNumber()}")
        for shape in footprint.GraphicalItems():
            add(shape, f"{key}/{segment_key(shape, footprint.GetPosition())}")
    for track in board.GetTracks():
        if isinstance(track, pcbnew.PCB_VIA):
            point = track.GetPosition()
            key = (
                f"via:{track.GetNetname()}:{point.x}:{point.y}:"
                f"{track.GetWidth(pcbnew.F_Cu)}:{track.GetDrillValue()}"
            )
        else:
            ends = sorted(
                (point.x, point.y) for point in (track.GetStart(), track.GetEnd())
            )
            key = (
                f"track:{track.GetNetname()}:{track.GetLayer()}:"
                f"{ends}:{track.GetWidth()}"
            )
        add(track, key)
    for drawing in board.GetDrawings():
        if isinstance(drawing, pcbnew.PCB_SHAPE):
            add(drawing, segment_key(drawing, pcbnew.VECTOR2I(0, 0)))
        elif isinstance(drawing, pcbnew.PCB_TEXT):
            point = drawing.GetPosition()
            add(
                drawing,
                f"text:{drawing.GetLayer()}:{drawing.GetText()}:{point.x}:{point.y}",
            )
        else:
            raise ValueError("unsupported board drawing for stable identity")
    for zone in board.Zones():
        add(zone, f"plane:{zone.GetNetname()}:{zone.GetLayer()}")
    return identities


def normalize_board_uuids(board: pcbnew.BOARD, path: Path) -> None:
    """Replace every serialized item UUID, refusing an unmapped native item."""
    identities = stable_uuid_map(board)
    source = path.read_text()
    found = set(_UUID_PATTERN.findall(source))
    if missing := found - identities.keys():
        raise ValueError(f"unmapped KiCad item UUIDs: {len(missing)}")
    normalized = _UUID_PATTERN.sub(
        lambda match: f'(uuid "{identities[match.group(1)]}")', source
    )
    path.write_text(order_footprints(normalized))
