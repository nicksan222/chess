"""Where every part sits on the board.

Coordinates are the same ones the mechanical design uses: the playing area is
centred on the origin and the control strip extends in negative Y. Translation
into the positive quadrant Gerber wants happens once, at write time.

Most of the board places itself. The 64 Hall sensors sit at square centres, the
64 LEDs sit at the offset the tile plate's diffuser pockets already assume, and
buttons remain at the positions the case bezel already drills. Those come from
shared
dimensions, so the copper cannot drift away from the plastic.

What does not place itself is the handful of one-off parts, which are laid out by
hand in `STRIP_LAYOUT` below. They all live on the control strip, because the
playing area is fully occupied by the grid: there is no free copper at the rear
edge for a power inlet.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING

import footprints
from core import sources, square

if TYPE_CHECKING:
    from core.kicad import KiCadBoard

EXPANDER_CAP_OFFSET_MM = (0.0, -12.0)

# One-off parts. Every position was chosen against the strip's other occupants
# and is checked for overlap by the tests rather than trusted.
STRIP_LAYOUT: dict[str, tuple[float, float, float]] = {
    # Power inlet, at the left edge so the barrel can reach the case wall.
    "J3": (-150.0, -178.0, 0.0),
    "F1": (-138.0, -178.0, 0.0),
    "D1": (-150.0, -165.0, 0.0),
    "SW13": (-113.0, -190.0, 0.0),
    "C1": (-128.0, -170.0, 0.0),
    "C2": (-116.0, -168.0, 0.0),
    # Display connector. The module itself is on a jumper, so only the header
    # has to be here; it does not have to sit under the bezel window.
    "J2": (-95.0, -172.0, 0.0),
    # LED level buffer, close to the Pi header it takes SPI from.
    "U5": (-70.0, -180.0, 0.0),
    "C7": (-58.0, -180.0, 0.0),
    "R1": (-50.0, -170.0, 0.0),
    "R2": (-50.0, -176.0, 0.0),
    "TP1": (-40.0, -165.0, 0.0),
    "TP2": (-33.0, -165.0, 0.0),
    "TP3": (-26.0, -165.0, 0.0),
    "TP4": (-19.0, -165.0, 0.0),
}

# The Pi header lies across the board on a grid line, where no Hall sensor sits.
# Its long axis runs across the board rather than along it.
PI_HEADER_ROTATION_DEG = 90.0


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
            yield pad.net_number, pad.number, (
                round(self.x + turned.x, 4),
                round(self.y + turned.y, 4),
            ), turned

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
            rotation = PI_HEADER_ROTATION_DEG
        elif reference in STRIP_LAYOUT:
            x, y, rotation = STRIP_LAYOUT[reference]
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
                expander_position[0] + EXPANDER_CAP_OFFSET_MM[0],
                expander_position[1] + EXPANDER_CAP_OFFSET_MM[1],
            )
        else:
            raise RuntimeError(
                f"{reference} ({entry['lib']}, {package}) has no placement rule"
            )

        placements.append(
            Placement(reference, package, position[0], position[1], rotation)
        )
    return placements
