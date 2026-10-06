"""Build the physical copper and guide marks KiCad needs for each component.

A *footprint* is the board drawing for one component: where its solderable metal
lands go, what shape they have, and outlines that help with assembly and spacing.
A *pad* is one of those metal lands. A component lead or soldered terminal touches
a pad; when the board is assembled, copper wiring connects pads to each other.
Through-hole pads have a drilled hole for a lead and copper around it. Surface-mount
pads are flat copper areas for parts soldered directly onto the board surface.

The component files in this folder provide dimensions measured from approved part
drawings. These helpers turn those dimensions into KiCad objects; they do not choose
or invent component dimensions. A courtyard is a keep-clear guide around a part so
nearby parts do not collide. The fabrication outline is a drawing guide for the part's
body. Silkscreen is the printed text/ink on the board, including the polarity dot.
A copper plane is a broad copper area used as a shared connection, often for power or
ground; thermal spokes are the narrow copper links between a pad and that plane.

Dimensions passed into these helpers are millimetres in the datasheet top view, where
positive Y points up. KiCad stores board Y in the opposite direction; `pad()` converts
coordinates at that boundary. `pcbnew` is KiCad's Python interface for creating the
actual board objects used by the rest of the PCB definition.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import pcbnew

from pcb.definition import rules

# Courtyard margin around pads/body; also the inset of the F.Fab outline.
COURTYARD_MARGIN_MM = 0.25

# Sullins .100" female header catalogue p81: recommended P.C. board hole Ø.040 [1.02].
SULLINS_HOLE_MM = 1.02

# Front-silk polarity dot beside pad 1 / cathode / "+". Its edge keeps the fab's
# mask dam beyond the pad's solder-mask opening, plus margin.
POLARITY_DOT_MM = 0.5

# Thermal spokes for pads that carry the 2 A board supply into a plane: 4 x 0.75 mm
# of 1 oz inner copper is 2.6 A at a 10 °C rise by IPC-2221 (tests/board/test_ampacity.py).
POWER_PAD_SPOKE_MM = 0.75

# Distance from a pad edge to the dot edge: the mask opening plus the fab's minimum mask
# dam plus 0.1 mm, so the dot never sits in the solder-mask opening.
POLARITY_DOT_GAP_MM = rules.MASK_EXPANSION_MM + rules.PCBWAY_MIN_MASK_DAM_MM + 0.1


def pad(
    number: str,
    x: float,
    y: float,
    width: float,
    height: float,
    shape: int = pcbnew.PAD_SHAPE_CIRCLE,
    drill: float = 0.0,
    drill_height: float = 0.0,
) -> pcbnew.PAD:
    """Create one numbered copper landing area for a component lead.

    `number` is the component pin number, which lets the schematic connection later
    identify this copper area. `(x, y)` is its centre; `width` and `height` are its
    size. `shape` controls whether KiCad draws it round, oval, or rectangular.
    A positive `drill` makes a plated through-hole: the lead passes through the board
    and can be soldered on either side. `drill_height` can make that hole a slot; if
    omitted, the hole is round. With no drill, this is a surface-mount landing for a
    lead soldered onto the board face.

    The pad's layer mask tells KiCad which copper layers it belongs to. Solder mask
    is the insulating coating that leaves the pad exposed; its small expansion makes
    sure the pad is not accidentally covered. Invalid numbering or dimensions are
    rejected instead of silently producing a bad land pattern.
    """
    # A missing second drill dimension means a round hole; a different height makes a slot.
    hole_height = drill_height or drill
    if (
        not number
        or min(width, height) <= 0
        or min(drill, hole_height) < 0
        or drill > width
        or hole_height > height
    ):
        raise ValueError(f"invalid pad dimensions: {number}")
    # Start a KiCad pad object, then give it its schematic pin number and board location.
    result = pcbnew.PAD(None)
    result.SetNumber(number)
    result.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(-y)))
    result.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(width), pcbnew.FromMM(height)))
    result.SetShape(shape)
    # A drilled pad spans copper on both board faces; an undrilled pad is top-side SMD copper.
    if drill:
        result.SetAttribute(pcbnew.PAD_ATTRIB_PTH)
        result.SetDrillSize(
            pcbnew.VECTOR2I(pcbnew.FromMM(drill), pcbnew.FromMM(hole_height))
        )
        if drill != hole_height:
            result.SetDrillShape(pcbnew.PAD_DRILL_SHAPE_OBLONG)
        result.SetLayerSet(result.PTHMask())
    else:
        result.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        result.SetLayerSet(result.SMDMask())
    result.SetLocalSolderMaskMargin(pcbnew.FromMM(rules.MASK_EXPANSION_MM))
    return result


def courtyard_for(
    pads: tuple[pcbnew.PAD, ...], body: tuple[float, float] = (0.0, 0.0)
) -> tuple[float, float]:
    """Return the width and height of a keep-clear box around the component.

    The box encloses both the outer edges of the copper pads and the stated component
    body size, then adds a small margin. PCB layout checks use this courtyard to warn
    when another component is placed too close. It is a guide, not copper or a board cut.
    """
    # Measure the farthest pad edge from the footprint origin on each axis.
    reach_x = max(pcbnew.ToMM(abs(p.GetPosition().x) + p.GetSize().x / 2) for p in pads)
    reach_y = max(pcbnew.ToMM(abs(p.GetPosition().y) + p.GetSize().y / 2) for p in pads)
    return (
        round(max(2 * reach_x, body[0]) + 2 * COURTYARD_MARGIN_MM, 3),
        round(max(2 * reach_y, body[1]) + 2 * COURTYARD_MARGIN_MM, 3),
    )


def footprint(
    package: str,
    description: str,
    pads: tuple[pcbnew.PAD, ...],
    courtyard: tuple[float, float],
) -> pcbnew.FOOTPRINT:
    """Build a reusable KiCad component drawing from its pads and guide outlines.

    `package` is the package description recorded for this part; later registry checks
    compare it with the approved product. `description` is a human-readable label.
    `pads` are the numbered copper places where the component's leads are soldered.
    `courtyard` is the (width, height) of the spacing guide, usually from
    `courtyard_for()`. The courtyard layer communicates placement clearance; the fab
    layer shows the approximate component body for assembly documentation. Neither
    outline is itself copper.
    """
    result = pcbnew.FOOTPRINT(None)
    result.SetField("Package", package)
    result.SetLibDescription(description)
    # Pads are the copper connection points; the outlines are documentation/spacing guides.
    for item in pads:
        result.Add(item)
    # Courtyard marks placement clearance; fabrication outline marks the component body area.
    for layer, inset, width in (
        (pcbnew.F_CrtYd, 0.0, rules.COURTYARD_LINE_MM),
        (pcbnew.F_Fab, COURTYARD_MARGIN_MM, rules.FAB_LINE_MM),
    ):
        x, y = courtyard[0] / 2 - inset, courtyard[1] / 2 - inset
        corners = ((-x, y), (x, y), (x, -y), (-x, -y))
        for start, end in zip(corners, (*corners[1:], corners[0]), strict=True):
            line = pcbnew.PCB_SHAPE(result)
            line.SetShape(pcbnew.SHAPE_T_SEGMENT)
            line.SetStart(
                pcbnew.VECTOR2I(pcbnew.FromMM(start[0]), pcbnew.FromMM(start[1]))
            )
            line.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(end[0]), pcbnew.FromMM(end[1])))
            line.SetLayer(layer)
            line.SetWidth(pcbnew.FromMM(width))
            result.Add(line)
    return result


def two_terminal_smd(
    package: str,
    description: str,
    pitch_mm: float,
    pad_size_mm: tuple[float, float],
    body_size_mm: tuple[float, float],
    pin_numbers: Sequence[str],
) -> pcbnew.FOOTPRINT:
    """Create two flat solder lands for a small two-lead surface-mount component.

    The pads sit equally far apart on either side of the origin. `pitch_mm` is the
    centre-to-centre distance; the size and body dimensions come from the part drawing.
    This pattern is used for parts such as chip resistors and ceramic capacitors.
    """
    if len(pin_numbers) != 2:
        raise ValueError(f"{package}: expected two pin numbers")
    if pitch_mm <= 0.0 or any(axis <= 0.0 for axis in (*pad_size_mm, *body_size_mm)):
        raise ValueError(f"{package}: dimensions must be positive")
    width, height = pad_size_mm
    pads = (
        pad(pin_numbers[0], -pitch_mm / 2.0, 0.0, width, height, pcbnew.PAD_SHAPE_RECT),
        pad(pin_numbers[1], pitch_mm / 2.0, 0.0, width, height, pcbnew.PAD_SHAPE_RECT),
    )
    return footprint(package, description, pads, courtyard_for(pads, body_size_mm))


def soic(
    package: str,
    description: str,
    ways: int,
    row_pitch_mm: float,
    body_size_mm: tuple[float, float],
    pin_numbers: Sequence[str],
    *,
    pin_pitch_mm: float = 1.27,
    pad_size_mm: tuple[float, float] = (1.55, 0.60),
) -> pcbnew.FOOTPRINT:
    """Create two opposing rows of flat pads for a small multi-lead IC package.

    `ways` is the total lead count and must be even. `row_pitch_mm` separates the two
    rows; `pin_pitch_mm` spaces neighbours along a row. Pin numbers are assigned in
    datasheet order: down the left row from pin 1, then up the right row. The first
    pad is rectangular as a visual pin-1 cue; the remaining pads are oval.
    """
    if ways <= 0 or ways % 2:
        raise ValueError(f"{package}: an SOIC needs a positive even pin count")
    if len(pin_numbers) != ways:
        raise ValueError(f"{package}: expected {ways} pin numbers")
    if row_pitch_mm <= 0.0 or pin_pitch_mm <= 0.0:
        raise ValueError(f"{package}: pitches must be positive")
    if any(axis <= 0.0 for axis in (*body_size_mm, *pad_size_mm)):
        raise ValueError(f"{package}: dimensions must be positive")

    # Numbering starts at pin 1 on the left and proceeds down that side, then up the right.
    per_side = ways // 2
    span = (per_side - 1) * pin_pitch_mm
    pad_width, pad_height = pad_size_mm
    pads: list[pcbnew.PAD] = []
    for index in range(per_side):
        number = pin_numbers[index]
        pads.append(
            pad(
                number,
                -row_pitch_mm / 2.0,
                span / 2.0 - index * pin_pitch_mm,
                pad_width,
                pad_height,
                pcbnew.PAD_SHAPE_RECT if number == "1" else pcbnew.PAD_SHAPE_OVAL,
            )
        )
    for index in range(per_side):
        pads.append(
            pad(
                pin_numbers[ways - index - 1],
                row_pitch_mm / 2.0,
                span / 2.0 - index * pin_pitch_mm,
                pad_width,
                pad_height,
                pcbnew.PAD_SHAPE_OVAL,
            )
        )
    finished = tuple(pads)
    return footprint(
        package, description, finished, courtyard_for(finished, body_size_mm)
    )


def two_pad_axial(
    package: str,
    description: str,
    pitch: float,
    lead_diameter: float,
    body: tuple[float, float],
    pin_numbers: Sequence[str],
) -> pcbnew.FOOTPRINT:
    """Create two drilled solder pads for a component with two wire leads.

    The holes sit on a horizontal line, separated by `pitch`; the component body size
    sets the keep-clear outline. The first pad is square so an assembler can tell the
    marked end from the second, round pad. The hole diameter is chosen from the lead
    diameter, and the surrounding copper ring follows the board's clearance rule.
    """
    from pcb.definition import rules

    if len(pin_numbers) != 2:
        raise ValueError(f"{package}: expected two pin numbers")
    # Choose a hole for the lead, then enough copper around it to meet the board annulus rule.
    drill = rules.drill_for_lead(lead_diameter)
    copper = rules.pad_for_drill(drill)
    pads = (
        pad(
            pin_numbers[0],
            -pitch / 2.0,
            0.0,
            copper,
            copper,
            pcbnew.PAD_SHAPE_RECT,
            drill,
        ),
        pad(
            pin_numbers[1],
            pitch / 2.0,
            0.0,
            copper,
            copper,
            pcbnew.PAD_SHAPE_CIRCLE,
            drill,
        ),
    )
    return footprint(
        package=package,
        description=description,
        pads=pads,
        courtyard=courtyard_for(pads, body),
    )


def pin_header(
    package: str,
    description: str,
    columns: int,
    rows: int,
    pitch: float = 2.54,
    lead_diameter: float = 0.64,
    pin_numbers: tuple[str, ...] = (),
    drill: float | None = None,
) -> pcbnew.FOOTPRINT:
    """Create a rectangular grid of drilled holes for a multi-pin socket/header.

    `columns` and `rows` set the grid dimensions, and `pitch` is the centre spacing.
    `pin_numbers` gives the logical name of each hole in numbering order. Numbering
    runs across the short direction first (pin 1 at the top left, pin 2 beside it),
    then continues down the next column. Pin 1 is square; the other holes are round.
    A drill is sized for the connector's metal pins, with enough surrounding copper
    to solder them to the board.
    """
    from pcb.definition import rules

    # `columns` runs along the long row; each column contains `rows` adjacent pins.
    count = columns * rows
    if len(pin_numbers) != count:
        raise ValueError(f"{package}: expected {count} semantic pin numbers")
    drill = drill if drill is not None else rules.drill_for_lead(lead_diameter)
    copper = rules.pad_for_drill(drill)
    span_x = (rows - 1) * pitch
    span_y = (columns - 1) * pitch
    pads: list[pcbnew.PAD] = []
    # Lay out each column top-to-bottom, numbering across each short row as the Pi does.
    for column in range(columns):
        for row in range(rows):
            number = column * rows + row + 1
            shape = pcbnew.PAD_SHAPE_RECT if number == 1 else pcbnew.PAD_SHAPE_CIRCLE
            pads.append(
                pad(
                    pin_numbers[number - 1],
                    -span_x / 2.0 + row * pitch,
                    span_y / 2.0 - column * pitch,
                    copper,
                    copper,
                    shape,
                    drill,
                )
            )
    return footprint(
        package=package,
        description=description,
        pads=tuple(pads),
        courtyard=courtyard_for(tuple(pads)),
    )


# Used to pick the polarity-dot position furthest from every other pad.
def _box_distance(x: float, y: float, pad: pcbnew.PAD) -> float:
    """Distance from a point to a pad's rectangular copper extent, in mm."""
    centre, size = pad.GetPosition(), pad.GetSize()
    # Distances inside the pad rectangle count as zero; outside, measure from its nearest edge.
    dx = max(abs(x - pcbnew.ToMM(centre.x)) - pcbnew.ToMM(size.x) / 2, 0.0)
    dy = max(abs(y - pcbnew.ToMM(centre.y)) - pcbnew.ToMM(size.y) / 2, 0.0)
    return math.hypot(dx, dy)


def add_polarity_marker(template: pcbnew.FOOTPRINT, number: str) -> None:
    """Add a printed board-top dot beside a pin that identifies the component's end.

    Assemblers use this mark to orient parts with a pin 1, positive terminal, or other
    special end. The helper tests the four directions around the selected pad and puts
    the dot on the outward side with the most room from other pads. It refuses to place
    the mark if it would be closer to another pad than to the selected pad.
    """
    pads = list(template.Pads())
    target = next(p for p in pads if p.GetNumber() == number)
    others = [p for p in pads if p is not target]
    cx, cy = pcbnew.ToMM(target.GetPosition().x), pcbnew.ToMM(target.GetPosition().y)
    half_x = pcbnew.ToMM(target.GetSize().x) / 2
    half_y = pcbnew.ToMM(target.GetSize().y) / 2
    reach = POLARITY_DOT_GAP_MM + POLARITY_DOT_MM / 2
    candidates = [
        (cx + half_x + reach, cy),
        (cx - half_x - reach, cy),
        (cx, cy + half_y + reach),
        (cx, cy - half_y - reach),
    ]
    # Keep the dot beyond the footprint centre so it indicates the marked end, not an interior gap.
    outward = [
        (x, y) for x, y in candidates if x * x + y * y > cx * cx + cy * cy + 1e-9
    ]

    def clearance(point: tuple[float, float]) -> float:
        return min((_box_distance(*point, p) for p in others), default=1e9)

    # Prefer the candidate with the most space from other pads, avoiding silkscreen-on-copper.
    x, y = max(outward, key=clearance)
    if clearance((x, y)) <= _box_distance(x, y, target):
        raise ValueError(f"pad {number}: polarity mark would sit nearer another pad")
    # KiCad draws the polarity dot as a short, thick silk segment rather than a filled circle.
    dot = pcbnew.PCB_SHAPE(template)
    dot.SetShape(pcbnew.SHAPE_T_SEGMENT)
    dot.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x - 0.01), pcbnew.FromMM(y)))
    dot.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x + 0.01), pcbnew.FromMM(y)))
    dot.SetLayer(pcbnew.F_SilkS)
    dot.SetWidth(pcbnew.FromMM(POLARITY_DOT_MM))
    template.Add(dot)


def widen_thermal_spokes(template: pcbnew.FOOTPRINT) -> None:
    """Make the copper links from this part's pads into a shared copper plane wider.

    When a pad connects to a large plane, KiCad can leave thin spokes between the pad
    and the surrounding copper to make soldering easier. Those thin links can restrict
    current. This override widens the links for supply-carrying parts; the ampacity test
    checks that the resulting copper can carry the intended current.
    """
    # Override each pad's plane spokes so the supply current can flow into copper planes.
    for item in template.Pads():
        item.SetLocalThermalSpokeWidthOverride(pcbnew.FromMM(POWER_PAD_SPOKE_MM))
