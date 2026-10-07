"""PCB-owned assembly metadata, readable by Blender's Python 3.11.

This snapshot is generated beside the checked KiCad model by the PCB build. It is derived data, never an
editable source, and contains no electrical implementation or KiCad dependency.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, cast

if TYPE_CHECKING:
    from pcb.board.board import Board

from shared import dimensions


@dataclass(frozen=True)
class PcbPart:
    reference: str
    value: str
    body_mm: tuple[float, float, float]
    position_mm: tuple[float, float]
    rotation_degrees: float
    bottom: bool
    housing_mm: tuple[float, float, float] | None = None
    panel_passage: str | None = None
    mated_zones: tuple[tuple[float, float, float, float], ...] = ()
    pin_positions_mm: dict[str, tuple[float, float]] = field(default_factory=dict)
    mated_zone_roles: tuple[str, ...] = ()
    wire_exit_mm: tuple[float, float] | None = None

    def __post_init__(self) -> None:
        if (
            not self.reference
            or not self.value
            or len(self.body_mm) != 3
            or len(self.position_mm) != 2
        ):
            raise ValueError("PCB snapshot requires identified bodies and placements")
        if (
            not all(
                math.isfinite(v)
                for v in (*self.body_mm, *self.position_mm, self.rotation_degrees)
            )
            or min(self.body_mm) <= 0
        ):
            raise ValueError("PCB snapshot dimensions must be finite and positive")


@dataclass(frozen=True)
class PcbSnapshot:
    parts: tuple[PcbPart, ...]
    sensors: dict[str, str]
    leds: dict[str, str]
    buttons: dict[str, str]
    host_header: str

    def __post_init__(self) -> None:
        names = {part.reference for part in self.parts}
        if not names or len(names) != len(self.parts):
            raise ValueError("PCB snapshot references must be nonempty and unique")
        grouped = {
            *self.sensors.values(),
            *self.leds.values(),
            *self.buttons.values(),
            self.host_header,
        }
        if grouped - names:
            raise ValueError("PCB snapshot groups contain unknown references")

    @classmethod
    def current(cls) -> PcbSnapshot:
        # This runs only in the host Python, never in Blender's Python 3.11.

        from pcb.board.board import Board

        return cls.from_board(Board())

    @classmethod
    def from_board(cls, board: Board) -> PcbSnapshot:
        from enum import StrEnum

        from pcb.harness import BoardComponent, Side

        parts: list[PcbPart] = []
        for component in board.components():
            part = cast(BoardComponent[StrEnum], component)
            parts.append(
                PcbPart(
                    part.reference,
                    part.definition.product.part_number,
                    part.definition.product.body_mm,
                    (
                        part.placement.x_mm,
                        part.placement.y_mm + dimensions.PCB_CENTER_OFFSET_Y_MM,
                    ),
                    part.placement.rotation_degrees,
                    part.placement.side is Side.BOTTOM,
                    next(
                        (
                            solid.size_mm
                            for solid in part.definition.model_3d.solids
                            if solid.name == "Body"
                        ),
                        None,
                    )
                    if part.definition.model_3d
                    else None,
                    part.definition.panel_passage,
                    tuple(
                        (zone.start_mm, zone.end_mm, zone.width_mm, zone.height_mm)
                        for zone in part.definition.mated_zones
                    ),
                    {
                        str(pin): (
                            part.pin_position(pin).x_mm,
                            part.pin_position(pin).y_mm
                            + dimensions.PCB_CENTER_OFFSET_Y_MM,
                        )
                        for pin in part.definition.pin_type
                    },
                    tuple(zone.role for zone in part.definition.mated_zones),
                    next(
                        (
                            (zone.start_mm, zone.height_mm)
                            for zone in part.definition.mated_zones
                            if zone.role == "wire_exit"
                        ),
                        None,
                    ),
                )
            )
        return cls(
            tuple(parts),
            {name: part.reference for name, part in board.sensors.items()},
            {name: part.reference for name, part in board.leds.items()},
            {name: part.reference for name, part in board.buttons.items()},
            board.host_header.reference,
        )

    def write(self, path: Path) -> None:
        path.write_text(json.dumps(asdict(self), indent=2) + "\n")

    @classmethod
    def read(cls, path: Path) -> PcbSnapshot:
        data = cast(dict[str, object], json.loads(path.read_text()))
        parts = tuple(
            PcbPart(
                cast(str, part["reference"]),
                cast(str, part["value"]),
                cast(
                    tuple[float, float, float],
                    tuple(cast(list[float], part["body_mm"])),
                ),
                cast(
                    tuple[float, float], tuple(cast(list[float], part["position_mm"]))
                ),
                cast(float, part["rotation_degrees"]),
                cast(bool, part["bottom"]),
                cast(
                    tuple[float, float, float],
                    tuple(cast(list[float], part["housing_mm"])),
                )
                if part.get("housing_mm")
                else None,
                cast(str | None, part.get("panel_passage")),
                tuple(
                    cast(tuple[float, float, float, float], tuple(zone))
                    for zone in cast(list[list[float]], part.get("mated_zones", []))
                ),
                {
                    pin: cast(tuple[float, float], tuple(position))
                    for pin, position in cast(
                        dict[str, list[float]], part.get("pin_positions_mm", {})
                    ).items()
                },
                tuple(cast(list[str], part.get("mated_zone_roles", []))),
                cast(
                    tuple[float, float], tuple(cast(list[float], part["wire_exit_mm"]))
                )
                if part.get("wire_exit_mm")
                else None,
            )
            for part in cast(list[dict[str, object]], data["parts"])
        )
        return cls(
            parts,
            cast(dict[str, str], data["sensors"]),
            cast(dict[str, str], data["leds"]),
            cast(dict[str, str], data["buttons"]),
            cast(str, data["host_header"]),
        )
