"""Preview declared electrical connections as airwires, never copper routing."""

from collections import defaultdict
from html import escape
from pathlib import Path

import pcbnew

from ...circuit import Circuit
from ...connections import NetConnection
from ...net import Net


def _airwires(
    points: set[tuple[float, float]],
) -> list[tuple[tuple[float, float], tuple[float, float]]]:
    """A minimum spanning tree keeps each net connected without duplicate lines."""
    if not points:
        return []
    remaining = set(points)
    first = min(remaining)
    remaining.remove(first)
    nearest = {point: first for point in remaining}
    result: list[tuple[tuple[float, float], tuple[float, float]]] = []
    while remaining:
        end = min(
            remaining,
            key=lambda point: (
                (point[0] - nearest[point][0]) ** 2
                + (point[1] - nearest[point][1]) ** 2,
                point,
            ),
        )
        result.append((nearest[end], end))
        remaining.remove(end)
        for point in remaining:
            if (point[0] - end[0]) ** 2 + (point[1] - end[1]) ** 2 < (
                point[0] - nearest[point][0]
            ) ** 2 + (point[1] - nearest[point][1]) ** 2:
                nearest[point] = end
    return result


def write_connections[BoardNet: Net](
    circuit: Circuit[BoardNet], board_path: Path, output: Path
) -> Path:
    """Draw the saved PCB's pad assignments with visible, labeled airwires."""
    outline = circuit.outline
    if outline is None:
        raise ValueError("connection preview needs a board outline")
    board = pcbnew.LoadBoard(str(board_path))
    connected_nets = {
        connection.net.label
        for component in circuit.components()
        for _, connection in component.pin_connections()
        if isinstance(connection, NetConnection)
    }
    points: dict[str, set[tuple[float, float]]] = defaultdict(set)
    labels: list[str] = []
    pads: list[str] = []
    for footprint in board.GetFootprints():
        position = footprint.GetPosition()
        x, y = pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)
        labels.append(
            f'<text x="{x:.3f}" y="{y - 2:.3f}">{escape(footprint.GetReference())}</text>'
        )
        for pad in footprint.Pads():
            position = pad.GetPosition()
            x, y = pcbnew.ToMM(position.x), pcbnew.ToMM(position.y)
            if pad.GetNetname() in connected_nets:
                points[pad.GetNetname()].add((x, y))
            pads.append(f'<circle cx="{x:.3f}" cy="{y:.3f}" r="0.35"/>')
    rows = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-8 -16 {outline.width_mm + 16} {outline.height_mm + 24}">',
        '<rect x="-8" y="-16" width="100%" height="100%" fill="#f8fafc"/>',
        '<text x="0" y="-8" font-size="3.5" font-family="sans-serif">Electrical connections (airwires); these are not copper traces</text>',
        f'<rect width="{outline.width_mm}" height="{outline.height_mm}" fill="white" stroke="#64748b" stroke-width="0.4"/>',
    ]
    for name, net_points in sorted(points.items()):
        power = name in {"GND", "+3V3", "+5V", "LED_5V"}
        rows.append(
            f'<g fill="none" stroke="{"#94a3b8" if power else "#0891b2"}" stroke-width="0.18" stroke-dasharray="0.8 0.4" opacity="{"0.35" if power else "0.8"}"><title>{escape(name)}</title>'
        )
        for start, end in _airwires(net_points):
            rows.append(
                f'<path d="M {start[0]:.3f} {start[1]:.3f} L {end[0]:.3f} {end[1]:.3f}"/>'
            )
        rows.append("</g>")
    rows.extend(
        (
            '<g fill="#334155">',
            *pads,
            "</g>",
            '<g fill="#0f172a" font-family="sans-serif" font-size="1.5" text-anchor="middle">',
            *labels,
            "</g>",
            "</svg>",
        )
    )
    output.write_text("\n".join(rows) + "\n")
    return output
