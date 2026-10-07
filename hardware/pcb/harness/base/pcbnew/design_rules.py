"""Circuit design limits and package-scoped KiCad rule generation."""

import json
import math
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import cast

from ..circuit import Circuit
from ..component import BoardComponent
from ..geometry import Side
from ..net import Net
from .routing.settings import RoutingSettings


@dataclass(frozen=True)
class DesignRules:
    routing: RoutingSettings
    hole_clearance_mm: float = 0.25
    hole_to_hole_mm: float = 0.25
    minimum_drill_mm: float = 0.2
    process_track_width_mm: float = 0.127
    process_clearance_mm: float = 0.152
    process_annular_ring_mm: float = 0.13

    def __post_init__(self) -> None:
        if any(
            not math.isfinite(value) or value <= 0
            for value in (
                self.hole_clearance_mm,
                self.hole_to_hole_mm,
                self.minimum_drill_mm,
                self.process_track_width_mm,
                self.process_clearance_mm,
                self.process_annular_ring_mm,
            )
        ):
            raise ValueError("design limits must be finite and positive")
        if (
            self.routing.track_width_mm < self.process_track_width_mm
            or self.routing.clearance_mm < self.process_clearance_mm
        ):
            raise ValueError("routing violates declared process floors")
        if (
            self.routing.via_drill_mm < self.minimum_drill_mm
            or (self.routing.via_diameter_mm - self.routing.via_drill_mm) / 2
            < self.process_annular_ring_mm
        ):
            raise ValueError("via violates declared drill or annular ring floor")

    def minimums[BoardNet: Net](
        self, circuit: Circuit[BoardNet]
    ) -> tuple[float, float]:
        clearance, width = self.routing.clearance_mm, self.routing.track_width_mm
        for placed in circuit.components():
            part = cast(BoardComponent[StrEnum], placed)
            exception = part.definition.routing.clearance
            if exception is not None:
                clearance = min(clearance, exception.clearance_mm)
                width = min(width, exception.track_width_mm)
        return clearance, width


def write_rules[BoardNet: Net](
    circuit: Circuit[BoardNet], rules: DesignRules, directory: Path, name: str
) -> None:
    parts = tuple(cast(BoardComponent[StrEnum], part) for part in circuit.components())
    exceptions = tuple(
        part for part in parts if part.definition.routing.clearance is not None
    )
    minimum_clearance = rules.routing.clearance_mm
    minimum_width = rules.routing.track_width_mm
    custom = [
        "(version 1)",
        '(rule "Board clearance"',
        f"  (constraint clearance (min {minimum_clearance}mm)))",
        '(rule "Board track width"',
        "  (condition \"A.Type == 'Track'\")",
        f"  (constraint track_width (min {minimum_width}mm)))",
    ]
    for part in exceptions:
        exception = part.definition.routing.clearance
        assert exception is not None
        if (
            exception.clearance_mm < rules.process_clearance_mm
            or exception.track_width_mm < rules.process_track_width_mm
        ):
            raise ValueError("package clearance violates declared process floors")
        minimum_clearance = min(minimum_clearance, exception.clearance_mm)
        minimum_width = min(minimum_width, exception.track_width_mm)
        ref = part.reference
        layer = "B.Cu" if part.placement.side is Side.BOTTOM else "F.Cu"

        def near(item: str, ref: str = ref) -> str:
            return f"{item}.memberOfFootprint('{ref}') || (({item}.Type == 'Track' || {item}.Type == 'Via') && {item}.intersectsCourtyard('{ref}'))"

        custom.extend(
            (
                f'(rule "{ref} fine-pitch clearance"',
                f'  (layer "{layer}")',
                f'  (condition "{near("A")} || {near("B")}")',
                f"  (constraint clearance (min {exception.clearance_mm}mm)))",
                f'(rule "{ref} escape track width"',
                f'  (layer "{layer}")',
                f"  (condition \"A.Type == 'Track' && A.intersectsCourtyard('{ref}')\")",
                f"  (constraint track_width (min {exception.track_width_mm}mm)))",
            )
        )
    path = directory / f"{name}.kicad_pro"
    project = cast(dict[str, object], json.loads(path.read_text()))
    settings = cast(
        dict[str, object], cast(dict[str, object], project["board"])["design_settings"]
    )
    limits = cast(dict[str, object], settings["rules"])
    limits.update(
        {
            "min_clearance": minimum_clearance,
            "min_track_width": minimum_width,
            "min_copper_edge_clearance": rules.routing.edge_clearance_mm,
            "min_hole_clearance": rules.hole_clearance_mm,
            "min_hole_to_hole": rules.hole_to_hole_mm,
            "min_through_hole_diameter": rules.minimum_drill_mm,
            "min_via_annular_width": round(
                (rules.routing.via_diameter_mm - rules.routing.via_drill_mm) / 2, 4
            ),
            "min_via_diameter": rules.routing.via_diameter_mm,
        }
    )
    settings["drc_exclusions"] = []
    net_settings = cast(dict[str, object], project["net_settings"])
    for netclass in cast(list[dict[str, object]], net_settings["classes"]):
        netclass.update(
            {
                "clearance": rules.routing.clearance_mm,
                "track_width": rules.routing.track_width_mm,
            }
        )
    path.write_text(json.dumps(project, indent=2) + "\n")
    (directory / f"{name}.kicad_dru").write_text("\n".join((*custom, "")))
