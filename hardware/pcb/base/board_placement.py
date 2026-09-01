"""KiCad-independent physical placement planning.

Coordinates use the shared mechanical origin: the playing area is centred and
the control strip extends in negative Y. Each board feature owns one small
placement rule; the coordinator rejects both missing and ambiguous ownership.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import ModuleType

from base import sources, square
from base.component import ComponentReference
from base.placement import Placement, PlacementPlanner, PlacementRule
from components import footprints


@dataclass(frozen=True)
class PlacementContext:
    """Shared immutable input available to focused placement rules."""

    dimensions: ModuleType
    components: Mapping[str, Mapping[str, object]]
    square_parts: Mapping[str, square.SquarePartPlacement]
    button_positions: Mapping[str, tuple[float, float]]


def _placement(
    reference: str,
    package: str,
    position: tuple[float, float],
    rotation: float = 0.0,
) -> Placement:
    return Placement(
        reference,
        package,
        position[0],
        position[1],
        rotation,
        footprints.for_package(package),
    )


def _package(reference: str, entry: Mapping[str, object]) -> str:
    package = entry.get("package")
    if not isinstance(package, str):
        raise ValueError(f"{reference}: package must be a string")
    return package


def _extras(reference: str, entry: Mapping[str, object]) -> Mapping[str, object]:
    extras = entry.get("extras")
    if not isinstance(extras, Mapping):
        raise ValueError(f"{reference}: extras must be a mapping")
    return extras


class SquarePlacementRule:
    """Place the four-part assembly repeated at each playing square."""

    def place(self, reference, entry, context):
        part = context.square_parts.get(reference)
        if part is None:
            return None
        return _placement(reference, part.package, (part.x, part.y), part.rotation)


class ExpanderPlacementRule:
    """Place each GPIO expander beside the quadrant it serves."""

    def place(self, reference, entry, context):
        quadrant = _extras(reference, entry).get("Quadrant")
        if quadrant is None:
            return None
        try:
            position = context.dimensions.EXPANDER_POSITIONS_BY_QUADRANT_MM[quadrant]
        except KeyError as error:
            raise RuntimeError(
                f"{reference}: unknown expander quadrant {quadrant!r}"
            ) from error
        return _placement(reference, _package(reference, entry), position)


class ControlPlacementRule:
    """Place front-panel controls beneath their matching case openings."""

    def place(self, reference, entry, context):
        function = _extras(reference, entry).get("Function")
        if function is None:
            return None
        try:
            position = context.button_positions[function]
        except KeyError as error:
            raise RuntimeError(f"{reference}: unknown control {function!r}") from error
        return _placement(reference, _package(reference, entry), position)


class HostPlacementRule:
    """Place and orient the Raspberry Pi GPIO header in its mechanical bay."""

    def place(self, reference, entry, context):
        if reference != ComponentReference.HOST_GPIO_HEADER:
            return None
        return _placement(
            reference,
            _package(reference, entry),
            context.dimensions.PI_BAY_CENTER_MM,
            context.dimensions.PI_HEADER_ROTATION_DEG,
        )


class StripPlacementRule:
    """Place one-off power, display, and bring-up parts on the control strip."""

    def place(self, reference, entry, context):
        raw = context.dimensions.PCB_STRIP_PLACEMENTS_MM.get(reference)
        if raw is None:
            return None
        x, y, rotation = raw
        return _placement(reference, _package(reference, entry), (x, y), rotation)


class ExpanderBypassPlacementRule:
    """Place each expander's local bypass capacitor beside its owning IC."""

    def place(self, reference, entry, context):
        expander_reference = _extras(reference, entry).get("For")
        if entry.get("lib") != "C" or expander_reference is None:
            return None
        try:
            expander = context.components[expander_reference]
        except KeyError as error:
            raise RuntimeError(
                f"{reference}: unknown decoupled component {expander_reference!r}"
            ) from error
        if expander.get("lib") != "MCP23017":
            raise RuntimeError(
                f"{reference}: decouples non-expander {expander_reference}"
            )
        quadrant = _extras(str(expander_reference), expander).get("Quadrant")
        expander_position = context.dimensions.EXPANDER_POSITIONS_BY_QUADRANT_MM[
            quadrant
        ]
        offset = context.dimensions.EXPANDER_CAP_OFFSET_MM
        position = (expander_position[0] + offset[0], expander_position[1] + offset[1])
        return _placement(reference, _package(reference, entry), position)


PLACEMENT_RULES: tuple[PlacementRule, ...] = (
    SquarePlacementRule(),
    ExpanderPlacementRule(),
    ControlPlacementRule(),
    HostPlacementRule(),
    StripPlacementRule(),
    ExpanderBypassPlacementRule(),
)


def square_centres(shared) -> dict[str, tuple[float, float]]:
    """Bridge mechanical far-side rows to electrical near-side rank names."""
    centres = {}
    for row, column, x, y in shared.BOARD_SQUARE_CENTERS_MM:
        name = f"{sources.names().FILES[column]}{shared.GRID_COUNT - row}"
        centres[name] = (x, y)
    return centres


def build(netlist: Mapping[str, object] | None = None) -> list[Placement]:
    """Plan every component and reject missing or ambiguous rule ownership."""
    dimensions = sources.dimensions()
    names = sources.names()
    netlist = netlist or sources.netlist()
    components = netlist["components"]
    centres = square_centres(dimensions)
    button_positions = dict(
        zip(names.BUTTON_NAMES, dimensions.PANEL_BUTTON_POSITIONS_MM, strict=True)
    )
    square_parts = {
        part.reference: part
        for assembly in square.build_all(
            components,
            centres,
            dimensions.LED_POSITION_MM,
        )
        for part in assembly.placements()
    }
    context = PlacementContext(
        dimensions,
        components,
        square_parts,
        button_positions,
    )

    return PlacementPlanner(PLACEMENT_RULES).plan(components, context)
