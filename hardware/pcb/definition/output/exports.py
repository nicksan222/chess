"""Purchasing, project settings, and review artwork exporters."""

from __future__ import annotations

import csv
import io
import json
import re
from collections import defaultdict
from pathlib import Path

import pcbnew

import pcb.definition.board as board_definition
from pcb.definition import rules
from pcb.definition.native import parts
from shared.components import COMPONENTS

EXTRA_ASSEMBLY_PARTS = ("PI_ZERO_2_W", "OLED_MODULE", "POWER_SUPPLY", "MICRO_SD")


def reference_sort_key(reference: str) -> tuple[str, int]:
    """Sort references naturally, including multi-letter prefixes such as HS."""
    prefix = reference.rstrip("0123456789")
    suffix = reference[len(prefix) :]
    return (prefix, int(suffix) if suffix else 0)


def _references_by_part(design: pcbnew.BOARD) -> dict[str, list[str]]:
    """Group only board-fitted references by approved product identity."""
    references: dict[str, list[str]] = defaultdict(list)
    for component in parts(design):
        references[component.GetFieldText("PartKey")].append(component.GetReference())
    return references


def render_bom(design: pcbnew.BOARD | None = None) -> str:
    design = design or board_definition.load()
    references = _references_by_part(design)
    for key in EXTRA_ASSEMBLY_PARTS:
        references[key].append("—")
    rows: list[str] = []
    for key in sorted(references):
        spec = COMPONENTS[key]
        refs = sorted(references[key], key=reference_sort_key)
        rows.append(
            f"| {len(refs)} | `{spec.mpn}` | {spec.manufacturer} | {spec.description} | {spec.package} | {', '.join(refs)} |"
        )
    text = [
        "# Approved bill of materials",
        "",
        "Generated from `hardware/shared/components.py` and `definition/board.py`.",
        "Every row names an exact manufacturer part number; substitutions require",
        "updating the shared catalog and passing footprint/package validation.",
        "",
        "| Qty | Manufacturer part number | Manufacturer | Description | Package | References |",
        "|---:|---|---|---|---|---|",
        *rows,
        "",
    ]
    return "\n".join(text)


def render_assembly_csv(design: pcbnew.BOARD | None = None) -> str:
    """Render a PCBWay-friendly BOM containing board-fitted parts only."""
    design = design or board_definition.load()
    references = _references_by_part(design)
    output = io.StringIO(newline="")
    writer = csv.writer(output, lineterminator="\n")
    writer.writerow(
        ("Item", "Quantity", "Reference", "Value", "Footprint", "Manufacturer", "MPN")
    )
    for item, key in enumerate(sorted(references), 1):
        spec = COMPONENTS[key]
        refs = sorted(references[key], key=reference_sort_key)
        writer.writerow(
            (
                item,
                len(refs),
                ",".join(refs),
                spec.description,
                spec.package,
                spec.manufacturer,
                spec.mpn,
            )
        )
    return output.getvalue()


STRICT_RULES = (
    "footprint_filters_mismatch",
    "footprint_type_mismatch",
    "missing_courtyard",
    "npth_inside_courtyard",
    "pth_inside_courtyard",
)


def render_project() -> str:
    project = json.loads(
        (Path(__file__).parents[2] / "definition/project-template.json").read_text()
    )
    settings = project["board"]["design_settings"]
    defaults = settings["defaults"]
    defaults.update(
        {
            "board_outline_line_width": rules.OUTLINE_LINE_MM,
            "courtyard_line_width": rules.COURTYARD_LINE_MM,
            "fab_line_width": rules.FAB_LINE_MM,
            "silk_line_width": rules.SILK_LINE_MM,
            "silk_text_size_h": rules.SILK_TEXT_HEIGHT_MM,
            "silk_text_size_v": rules.SILK_TEXT_HEIGHT_MM,
            "silk_text_thickness": rules.SILK_LINE_MM,
        }
    )
    defaults["zones"]["min_clearance"] = rules.POUR_CLEARANCE_MM
    constraints = settings["rules"]
    constraints.update(
        {
            "min_clearance": rules.CLEARANCE_MM,
            "min_copper_edge_clearance": rules.POUR_TO_OUTLINE_MM,
            "min_hole_clearance": rules.HOLE_CLEARANCE_MM,
            "min_hole_to_hole": rules.HOLE_TO_HOLE_MM,
            "min_silk_clearance": rules.PCBWAY_MIN_MASK_DAM_MM,
            "min_text_height": rules.PCBWAY_MIN_SILK_TEXT_HEIGHT_MM,
            "min_text_thickness": rules.PCBWAY_MIN_SILK_LINE_MM,
            "min_through_hole_diameter": rules.PCBWAY_MIN_DRILL_MM,
            "min_track_width": rules.TRACE_WIDTH_MM,
            "min_via_annular_width": rules.annular_ring(
                rules.VIA_PAD_MM, rules.VIA_DRILL_MM
            ),
            "min_via_diameter": rules.VIA_PAD_MM,
        }
    )
    settings["drc_exclusions"] = []
    for name in STRICT_RULES:
        settings["rule_severities"][name] = "error"
    return json.dumps(project, indent=2, sort_keys=True) + "\n"


SUBSTRATE_PATTERN = re.compile(
    '^\\s*<rect (?:id="board-substrate" )?x="0" .*?fill="#164936"/>\\n', re.MULTILINE
)

HEADER_MARKER = "  <desc>Image generated by PCBNEW </desc>\n"


def polish_svg(text: str, side: str) -> str:
    """Add deterministic review metadata and exactly one board substrate."""
    match = re.search('viewBox="([^"]+)"', text)
    if not match:
        raise ValueError("SVG has no viewBox")
    _x, _y, width, height = match.group(1).split()
    text = re.sub(
        "<title>.*?</title>",
        f"<title>Chess board PCB — {side} copper review</title>",
        text,
        count=1,
    )
    text = SUBSTRATE_PATTERN.sub("", text)
    substrate = f'  <rect id="board-substrate" x="0" y="0" width="{width}" height="{height}" rx="2" fill="#164936"/>\n'
    if HEADER_MARKER not in text:
        raise ValueError("SVG has an unexpected KiCad header")
    polished = text.replace(HEADER_MARKER, HEADER_MARKER + substrate, 1)
    return "\n".join(line.rstrip() for line in polished.splitlines()) + "\n"


def polish(path: Path, side: str) -> None:
    try:
        polished = polish_svg(path.read_text(), side)
    except ValueError as error:
        raise RuntimeError(f"{path}: {error}") from error
    path.write_text(polished)
