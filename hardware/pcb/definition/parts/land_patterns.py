"""Small native land-pattern constructors; pcbnew owns every physical definition."""

from __future__ import annotations

from collections.abc import Sequence

import pcbnew

from pcb.definition import rules

COURTYARD_MARGIN_MM = 0.25


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
    """Build a leaded part lying flat, with both holes on the X axis."""
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
) -> pcbnew.FOOTPRINT:
    """A pin header numbered the way a Raspberry Pi header is: odd, even, odd.

    Pin 1 sits at the top left, pin 2 beside it, and numbering advances along
    the short axis first.
    """
    from pcb.definition import rules

    count = columns * rows
    if len(pin_numbers) != count:
        raise ValueError(f"{package}: expected {count} semantic pin numbers")
    drill = rules.drill_for_lead(lead_diameter)
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
