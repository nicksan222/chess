"""Where every part sits on the board.

Coordinates are the same ones the mechanical design uses: the playing area is
centred on the origin and the control strip extends in negative Y. Translation
into the positive quadrant Gerber wants happens once, at write time.

Most of the board places itself. The 64 reeds sit at square centres, the 64 LEDs
at the offset the tile plate's diffuser pockets already assume, and the buttons at
the positions the case bezel already drills. Those come from the shared
dimensions, so the copper cannot drift away from the plastic.

What does not place itself is the handful of one-off parts, which are laid out by
hand in `STRIP_LAYOUT` below. They all live on the control strip, because the
playing area is fully occupied by the grid: there is no free copper at the rear
edge for a power inlet.
"""

from __future__ import annotations

from dataclasses import dataclass

import footprints
from core import sources

# Repeated parts, positioned relative to the square they serve.
LED_CAP_OFFSET_MM = (0.0, -8.0)
EXPANDER_OFFSET_MM = (14.0, 0.0)
EXPANDER_CAP_OFFSET_MM = (23.0, 0.0)

# One-off parts. Every position was chosen against the strip's other occupants
# and is checked for overlap by the tests rather than trusted.
STRIP_LAYOUT: dict[str, tuple[float, float, float]] = {
    # Power inlet, at the left edge so the barrel can reach the case wall.
    "J3": (-150.0, -178.0, 0.0),
    "F1": (-144.0, -193.0, 0.0),
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

# The Pi header lies across the board on a grid line, where no reed sits. It is
# rotated so the Pi's long axis runs across the board rather than along it.
PI_HEADER_ROTATION_DEG = 90.0

# Sockets are not placed. A socket occupies exactly the pads of the chip it
# holds, so placing both would put two footprints on one set of holes.
SKIPPED_LIBS = frozenset({"DIP_SOCKET"})


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


def _quadrant_centre(quadrant: str, shared) -> tuple[float, float]:
    """The centre of the 4x4 block an expander serves, from its label."""
    first, last = quadrant.split("-")
    centres = square_centres(shared)
    (x0, y0), (x1, y1) = centres[first], centres[last]
    return ((x0 + x1) / 2.0, (y0 + y1) / 2.0)


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

    placements: list[Placement] = []
    for reference, entry in sorted(components.items()):
        if entry["lib"] in SKIPPED_LIBS:
            continue
        package = entry["package"]
        extras = entry["extras"]
        rotation = 0.0

        if "Square" in extras:
            centre = centres[extras["Square"]]
            if entry["lib"] == "SK9822":
                position = (
                    centre[0] + shared.LED_POSITION_MM[0],
                    centre[1] + shared.LED_POSITION_MM[1],
                )
                # The chain serpentines: LEDs on even-numbered ranks face left
                # so each output points toward the following square.
                if int(extras["Square"][1:]) % 2 == 0:
                    rotation = 180.0
            elif entry["lib"] == "REED":
                position = centre
            elif entry["lib"] == "C":
                position = (
                    centre[0] + shared.LED_POSITION_MM[0] + LED_CAP_OFFSET_MM[0],
                    centre[1] + shared.LED_POSITION_MM[1] + LED_CAP_OFFSET_MM[1],
                )
            else:
                raise RuntimeError(f"{reference}: no rule for a per-square {entry['lib']}")
        elif "Quadrant" in extras:
            quadrant = _quadrant_centre(extras["Quadrant"], shared)
            position = (
                quadrant[0] + EXPANDER_OFFSET_MM[0],
                quadrant[1] + EXPANDER_OFFSET_MM[1],
            )
        elif "Function" in extras:
            position = button_positions[extras["Function"]]
        elif reference == "J1":
            position = shared.PI_BAY_CENTER_MM
            rotation = PI_HEADER_ROTATION_DEG
        elif reference in STRIP_LAYOUT:
            x, y, rotation = STRIP_LAYOUT[reference]
            position = (x, y)
        elif entry["lib"] == "C" and reference in _expander_cap_references(components):
            quadrant = _quadrant_centre(
                _expander_cap_quadrant(reference, components), shared
            )
            position = (
                quadrant[0] + EXPANDER_CAP_OFFSET_MM[0],
                quadrant[1] + EXPANDER_CAP_OFFSET_MM[1],
            )
        else:
            raise RuntimeError(
                f"{reference} ({entry['lib']}, {package}) has no placement rule"
            )

        placements.append(
            Placement(reference, package, position[0], position[1], rotation)
        )
    return placements


def _expander_cap_references(components: dict) -> dict[str, str]:
    """Decoupling capacitors that belong to an expander, by reference.

    The design contract numbers them alongside the expanders, so the pairing is by
    order rather than by an explicit field.
    """
    expanders = sorted(
        reference
        for reference, entry in components.items()
        if entry["lib"] == "MCP23017"
    )
    caps = sorted(
        (reference for reference, entry in components.items()
         if entry["lib"] == "C" and "Square" not in entry["extras"]),
        key=lambda reference: int(reference[1:]),
    )
    # C1, C2 and C7 are power and buffer parts placed by hand on the strip.
    quadrant_caps = [
        reference for reference in caps if reference not in STRIP_LAYOUT
    ]
    return dict(zip(quadrant_caps, expanders, strict=True))


def _expander_cap_quadrant(reference: str, components: dict) -> str:
    expander = _expander_cap_references(components)[reference]
    return components[expander]["extras"]["Quadrant"]
