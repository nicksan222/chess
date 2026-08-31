"""Copper this domain can route on its own, and the silkscreen that labels it.

Stage one deliberately routes only what the board's regularity makes
unambiguous, and reports everything else as outstanding rather than guessing:

- **The LED chain.** Consecutive LEDs in the serpentine are always exactly one
  square pitch apart, and always either along a rank or straight up a file, so
  clock and data need no obstacle reasoning at all.
- **Ground.** Every through-hole pad on ground already reaches the bottom pour,
  so those need no trace. Surface-mount ground pads get a stub and a via.

What is not routed here is the 64 reed sense lines, the I2C and SPI buses, and
5 V distribution. Those compete for the same top-layer space and need a router
that reasons about obstacles. `core/connectivity.py` reports them as unrouted,
and the fabrication package stays gated until they are done.

Everything below is driven by the published connection list rather than by
rebuilding the schematic's intent here. Routing what the schematic says, instead
of what this module believes it says, is what stops the two drifting apart.
"""

from __future__ import annotations

from core import nets, rules, sources, text
from core.layers import Artwork, Board, Trace, Via
from core.placement import Placement, square_centres
from footprints.sk9822 import CHAIN_PINS

GROUND_STUB_MM = 1.8
LABEL_INSET_MM = 3.5

def pad_positions(
    placements: list[Placement],
) -> dict[tuple[str, str], tuple[float, float]]:
    """Board coordinates of every pad, keyed by reference and schematic pin."""
    positions: dict[tuple[str, str], tuple[float, float]] = {}
    for placement in placements:
        for net_number, _number, position, _pad in placement.pads():
            positions.setdefault((placement.reference, net_number), position)
    return positions


def surface_mount_pads(placements: list[Placement]) -> set[tuple[str, str]]:
    found = set()
    for placement in placements:
        for net_number, _number, _position, pad in placement.pads():
            if not pad.plated_through:
                found.add((placement.reference, net_number))
    return found


def _dogleg(
    net: str, start: tuple[float, float], end: tuple[float, float]
) -> list[Trace]:
    """A straight run when the pads line up, otherwise two orthogonal segments."""
    if abs(start[1] - end[1]) < 1e-6 or abs(start[0] - end[0]) < 1e-6:
        return [Trace(net, "top", start, end)]
    corner = (end[0], start[1])
    return [Trace(net, "top", start, corner), Trace(net, "top", corner, end)]


def route_led_chain(placements: list[Placement], artwork: Artwork) -> int:
    """Wire every two-pad link between adjacent LEDs in the chain."""
    netlist = sources.netlist()
    positions = pad_positions(placements)
    led_references = {
        reference
        for reference, entry in netlist["components"].items()
        if entry["lib"] == "SK9822"
    }

    routed = 0
    for connection in netlist["connections"]:
        pads = [tuple(pad) for pad in connection["pads"]]
        if len(pads) != 2:
            continue
        if not all(reference in led_references for reference, _pin in pads):
            continue
        if not all(pin in CHAIN_PINS for _reference, pin in pads):
            continue
        name = connection["name"] or f"{pads[0][0]}-{pads[1][0]}"
        artwork.traces += _dogleg(name, positions[pads[0]], positions[pads[1]])
        routed += 1
    return routed


def stitch_ground(placements: list[Placement], artwork: Artwork) -> int:
    """Give every surface-mount ground pad a stub and a via into the pour."""
    pad_net = nets.pad_nets()
    positions = pad_positions(placements)
    board = Board()

    stitched = 0
    for key in sorted(surface_mount_pads(placements)):
        if not nets.is_ground(pad_net.get(key)):
            continue
        x, y = positions[key]
        # Away from the part body, on the side the LED's ground pad already
        # faces, so the stub never crosses the chain running past it.
        via_at = (x, y - GROUND_STUB_MM)
        if not board.contains(*via_at, margin=rules.POUR_TO_OUTLINE_MM):
            via_at = (x, y + GROUND_STUB_MM)
        artwork.traces.append(Trace(nets.GROUND_NET, "top", (x, y), via_at))
        artwork.vias.append(Via(nets.GROUND_NET, via_at))
        stitched += 1
    return stitched


def add_silkscreen(artwork: Artwork) -> None:
    """Draw the grid and label every file and rank.

    The labels are the point: they let an assembler tell which of 64 identical
    reed positions they are looking at without consulting a drawing.
    """
    shared = sources.dimensions()
    half = shared.PLAYING_SPAN_MM / 2.0
    pitch = shared.SQUARE_SIZE_MM
    height = rules.SILK_TEXT_HEIGHT_MM

    for index in range(shared.GRID_COUNT + 1):
        offset = -half + index * pitch
        artwork.silk_lines.append(((offset, -half), (offset, half)))
        artwork.silk_lines.append(((-half, offset), (half, offset)))

    # Labels sit just *inside* the playing area, not outside it. The board is
    # exactly as wide as the grid, so there is no margin to put them in: outside
    # the edge means outside the board, where a fab trims the silkscreen away.
    centres = square_centres(shared)
    files = sources.names().FILES
    for column in range(shared.GRID_COUNT):
        letter = files[column]
        x, _y = centres[f"{letter}1"]
        artwork.silk_lines += text.text_segments(
            letter, x, -half + LABEL_INSET_MM, height
        )
    for rank in range(1, shared.GRID_COUNT + 1):
        _x, y = centres[f"A{rank}"]
        artwork.silk_lines += text.text_segments(
            str(rank), -half + LABEL_INSET_MM, y, height
        )


def build_artwork(placements: list[Placement]) -> tuple[Artwork, dict[str, int]]:
    artwork = Artwork()
    counts = {
        "led_chain_links": route_led_chain(placements, artwork),
        "ground_stitches": stitch_ground(placements, artwork),
    }
    add_silkscreen(artwork)
    counts["traces"] = len(artwork.traces)
    counts["vias"] = len(artwork.vias)
    counts["silk_segments"] = len(artwork.silk_lines)
    return artwork, counts
