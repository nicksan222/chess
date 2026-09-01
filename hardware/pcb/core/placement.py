"""Where every part sits on the board.

Coordinates are the same ones the mechanical design uses: the playing area is
centred on the origin and the control strip extends in negative Y. Translation
into the positive quadrant Gerber wants happens once, at write time.

Most of the board places itself. The 64 Hall sensors sit at square centres, the
64 LEDs sit at the offset the tile plate's diffuser pockets already assume, and
buttons remain at the positions the case bezel already drills. Those come from
shared
dimensions, so the copper cannot drift away from the plastic.

The handful of one-off parts use the shared strip placement map, allowing CAD
and PCB generation to agree on connector access and occupied volume.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

import footprints
from core import sources, square

if TYPE_CHECKING:
    from core.kicad import KiCadBoard


@dataclass(frozen=True)
class Placement:
    """One part, positioned and oriented on the board."""

    reference: str
    package: str
    x: float
    y: float
    rotation: float

    @property
    def footprint(self) -> footprints.Footprint:
        return footprints.for_package(self.package)

    def pads(self):
        """This part's pads in board coordinates."""
        for pad in self.footprint.pads:
            turned = pad.rotated(self.rotation)
            yield (
                pad.net_number,
                pad.number,
                (
                    round(self.x + turned.x, 4),
                    round(self.y + turned.y, 4),
                ),
                turned,
            )

    def attach_to(
        self,
        board: KiCadBoard,
        component_entry: Mapping[str, object],
    ) -> None:
        """Materialize this component through the native KiCad adapter."""
        board.attach_component(self, component_entry)

    def courtyard(self) -> tuple[float, float, float, float]:
        """Bounding box as (x_min, y_min, x_max, y_max)."""
        width, height = self.footprint.courtyard_at(self.rotation)
        return (
            self.x - width / 2.0,
            self.y - height / 2.0,
            self.x + width / 2.0,
            self.y + height / 2.0,
        )


def square_centres(shared) -> dict[str, tuple[float, float]]:
    """Square name to its centre, bridging the two domains' row conventions.

    The mechanical design counts rows from the far side of the board, while the
    electrical design names ranks from the near side. This is the one place that
    difference is reconciled.
    """
    centres = {}
    for row, column, x, y in shared.BOARD_SQUARE_CENTERS_MM:
        name = f"{sources.names().FILES[column]}{shared.GRID_COUNT - row}"
        centres[name] = (x, y)
    return centres


def build() -> list[Placement]:
    """Every part the board carries, positioned."""
    shared = sources.dimensions()
    names = sources.names()
    netlist = sources.netlist()
    components = netlist["components"]
    centres = square_centres(shared)
    button_positions = dict(
        zip(names.BUTTON_NAMES, shared.PANEL_BUTTON_POSITIONS_MM, strict=True)
    )
    square_parts = {
        part.reference: part
        for assembly in square.build_all(
            components,
            centres,
            shared.LED_POSITION_MM,
        )
        for part in assembly.placements()
    }

    placements: list[Placement] = []
    for reference, entry in sorted(components.items()):
        package = entry["package"]
        extras = entry["extras"]
        rotation = 0.0

        if reference in square_parts:
            square_part = square_parts[reference]
            position = (square_part.x, square_part.y)
            rotation = square_part.rotation
        elif "Quadrant" in extras:
            quadrant = extras["Quadrant"]
            try:
                position = shared.EXPANDER_POSITIONS_BY_QUADRANT_MM[quadrant]
            except KeyError as error:
                raise RuntimeError(
                    f"{reference}: unknown expander quadrant {quadrant!r}"
                ) from error
        elif "Function" in extras:
            position = button_positions[extras["Function"]]
        elif reference == "J1":
            position = shared.PI_BAY_CENTER_MM
            rotation = shared.PI_HEADER_ROTATION_DEG
        elif reference in shared.PCB_STRIP_PLACEMENTS_MM:
            x, y, rotation = shared.PCB_STRIP_PLACEMENTS_MM[reference]
            position = (x, y)
        elif entry["lib"] == "C" and "For" in extras:
            expander_reference = extras["For"]
            expander = components[expander_reference]
            if expander["lib"] != "MCP23017":
                raise RuntimeError(
                    f"{reference}: decouples non-expander {expander_reference}"
                )
            expander_position = shared.EXPANDER_POSITIONS_BY_QUADRANT_MM[
                expander["extras"]["Quadrant"]
            ]
            position = (
                expander_position[0] + shared.EXPANDER_CAP_OFFSET_MM[0],
                expander_position[1] + shared.EXPANDER_CAP_OFFSET_MM[1],
            )
        else:
            raise RuntimeError(
                f"{reference} ({entry['lib']}, {package}) has no placement rule"
            )

        placements.append(
            Placement(reference, package, position[0], position[1], rotation)
        )
    return placements
