"""Small native land-pattern constructors; pcbnew owns every physical definition.

Role: the helpers every `parts/<component>.py` uses to build a footprint template: a pad
constructor with sanity checks, a courtyard calculation, generic SOIC/two-terminal/axial/
header builders, the silkscreen polarity dot, and the wide thermal-spoke override for
power-carrying parts. Dimensions arrive from the caller (cited from datasheets in each part
file); nothing here invents a land pattern. Footprint coordinates are millimetres, Y up in
the datasheet "top view", converted to KiCad's Y-down units inside `pad()`.
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
    """One pad at (x, y) mm, Y up, of `width` x `height`, optionally drilled.

    `drill > 0` makes a plated through-hole pad on all layers (round, or oblong when
    `drill_height` differs); otherwise a surface-mount pad on the top layer. Raises on an
    empty number, non-positive size or a drill larger than the pad. Every pad gets the default local
    solder-mask expansion (callers may override it, as the eFuse does) so mask webs are consistent.
    """
    hole_height = drill_height or drill
    if (
        not number
        or min(width, height) <= 0
        or min(drill, hole_height) < 0
        or drill > width
        or hole_height > height
    ):
        raise ValueError(f"invalid pad dimensions: {number}")
    result = pcbnew.PAD(None)
    result.SetNumber(number)
    result.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x), pcbnew.FromMM(-y)))
    result.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(width), pcbnew.FromMM(height)))
    result.SetShape(shape)
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
    """Courtyard (width, height) enclosing all pads and the body, plus the margin."""
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
    """Assemble a footprint template from pads plus courtyard and fab outlines.

    `package` must equal the approved product's package string (`PcbPart` checks it);
    `courtyard` is (width, height) from `courtyard_for`.
    """
    result = pcbnew.FOOTPRINT(None)
    result.SetField("Package", package)
    result.SetLibDescription(description)
    for item in pads:
        result.Add(item)
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
    """Build a symmetric two-terminal chip land pattern."""
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
    """Build an SOIC with counter-clockwise datasheet pin numbering."""
    if ways <= 0 or ways % 2:
        raise ValueError(f"{package}: an SOIC needs a positive even pin count")
    if len(pin_numbers) != ways:
        raise ValueError(f"{package}: expected {ways} pin numbers")
    if row_pitch_mm <= 0.0 or pin_pitch_mm <= 0.0:
        raise ValueError(f"{package}: pitches must be positive")
    if any(axis <= 0.0 for axis in (*body_size_mm, *pad_size_mm)):
        raise ValueError(f"{package}: dimensions must be positive")

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
    """Build a leaded part lying flat, with both holes on the X axis.

    Pad 1 is square as the polarity cue; drill and copper ring follow `rules` from the
    lead diameter.
    """
    from pcb.definition import rules

    if len(pin_numbers) != 2:
        raise ValueError(f"{package}: expected two pin numbers")
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
    """A pin header numbered the way a Raspberry Pi header is: odd, even, odd.

    Pin 1 sits at the top left, pin 2 beside it, and numbering advances along
    the short axis first.
    """
    from pcb.definition import rules

    count = columns * rows
    if len(pin_numbers) != count:
        raise ValueError(f"{package}: expected {count} semantic pin numbers")
    drill = drill if drill is not None else rules.drill_for_lead(lead_diameter)
    copper = rules.pad_for_drill(drill)
    span_x = (rows - 1) * pitch
    span_y = (columns - 1) * pitch
    pads: list[pcbnew.PAD] = []
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
    dx = max(abs(x - pcbnew.ToMM(centre.x)) - pcbnew.ToMM(size.x) / 2, 0.0)
    dy = max(abs(y - pcbnew.ToMM(centre.y)) - pcbnew.ToMM(size.y) / 2, 0.0)
    return math.hypot(dx, dy)


def add_polarity_marker(template: pcbnew.FOOTPRINT, number: str) -> None:
    """Put one silk dot just outside pad `number`, on its most open outward side."""
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
    outward = [
        (x, y) for x, y in candidates if x * x + y * y > cx * cx + cy * cy + 1e-9
    ]

    def clearance(point: tuple[float, float]) -> float:
        return min((_box_distance(*point, p) for p in others), default=1e9)

    x, y = max(outward, key=clearance)
    if clearance((x, y)) <= _box_distance(x, y, target):
        raise ValueError(f"pad {number}: polarity mark would sit nearer another pad")
    dot = pcbnew.PCB_SHAPE(template)
    dot.SetShape(pcbnew.SHAPE_T_SEGMENT)
    dot.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(x - 0.01), pcbnew.FromMM(y)))
    dot.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(x + 0.01), pcbnew.FromMM(y)))
    dot.SetLayer(pcbnew.F_SilkS)
    dot.SetWidth(pcbnew.FromMM(POLARITY_DOT_MM))
    template.Add(dot)


def widen_thermal_spokes(template: pcbnew.FOOTPRINT) -> None:
    """Give every pad of a supply-path part the power spoke width.

    The default thermal spokes of a plane connection are too narrow to carry the 2 A
    supply; `tests/board/test_ampacity.py` checks the resulting plane entry.
    """
    for item in template.Pads():
        item.SetLocalThermalSpokeWidthOverride(pcbnew.FromMM(POWER_PAD_SPOKE_MM))
