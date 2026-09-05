"""KiCad-independent physical placement planning.

Coordinates use the shared mechanical origin: the playing area is centred and
the control strip extends in negative Y. Each board feature owns one small
placement rule; the coordinator rejects both missing and ambiguous ownership.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from board import square
from components import catalog
from components.tca9554 import Tca9554
from domain import sources
from domain.component import ComponentReference
from domain.placement import Placement, PlacementPlanner, PlacementRule
from domain.validation import is_string_mapping


@dataclass(frozen=True)
class PlacementContext:
    """Shared immutable input available to focused placement rules."""

    dimensions: sources.DimensionsSource
    components: Mapping[str, Mapping[str, object]]
    square_parts: Mapping[str, square.SquarePartPlacement]
    button_positions: Mapping[str, tuple[float, float]]


def _placement(
    reference: str,
    entry: Mapping[str, object],
    position: tuple[float, float],
    rotation: float = 0.0,
) -> Placement:
    """Place a product using the land pattern owned by its component class."""
    package = _package(reference, entry)
    model = catalog.for_netlist_entry(reference, entry)
    return Placement(
        reference,
        package,
        position[0],
        position[1],
        rotation,
        model.footprint_for(package),
    )


def _package(reference: str, entry: Mapping[str, object]) -> str:
    package = entry.get("package")
    if not isinstance(package, str):
        raise ValueError(f"{reference}: package must be a string")
    return package


def _extras(reference: str, entry: Mapping[str, object]) -> Mapping[str, object]:
    extras = entry.get("extras")
    if not is_string_mapping(extras):
        raise ValueError(f"{reference}: extras must have string keys")
    return extras


def _component_entries(
    contract: Mapping[str, object],
) -> Mapping[str, Mapping[str, object]]:
    raw = contract.get("components")
    if not is_string_mapping(raw):
        raise ValueError("board components must have string references")
    result: dict[str, Mapping[str, object]] = {}
    for reference, entry in raw.items():
        if not is_string_mapping(entry):
            raise ValueError(f"{reference}: component must have string keys")
        result[reference] = entry
    return result


class SquarePlacementRule:
    """Place the four-part assembly repeated at each playing square."""

    def place(
        self,
        reference: str,
        entry: Mapping[str, object],
        context: PlacementContext,
    ) -> Placement | None:
        part = context.square_parts.get(reference)
        if part is None:
            return None
        return _placement(reference, entry, (part.x, part.y), part.rotation)


class ExpanderPlacementRule:
    """Place each GPIO expander beside the bank it serves."""

    def place(
        self,
        reference: str,
        entry: Mapping[str, object],
        context: PlacementContext,
    ) -> Placement | None:
        bank = _extras(reference, entry).get("Bank")
        if bank is None:
            return None
        if not isinstance(bank, str):
            raise ValueError(f"{reference}: bank must be a string")
        try:
            position = context.dimensions.EXPANDER_POSITIONS_BY_BANK_MM[bank]
        except KeyError as error:
            raise RuntimeError(
                f"{reference}: unknown expander bank {bank!r}"
            ) from error
        return _placement(reference, entry, (position[0], position[1]))


class ControlPlacementRule:
    """Place front-panel controls beneath their matching case openings."""

    def place(
        self,
        reference: str,
        entry: Mapping[str, object],
        context: PlacementContext,
    ) -> Placement | None:
        function = _extras(reference, entry).get("Function")
        if function is None:
            return None
        if not isinstance(function, str):
            raise ValueError(f"{reference}: function must be a string")
        try:
            position = context.button_positions[function]
        except KeyError as error:
            raise RuntimeError(f"{reference}: unknown control {function!r}") from error
        return _placement(reference, entry, position)


class HostPlacementRule:
    """Place and orient the Raspberry Pi GPIO header in its mechanical bay."""

    def place(
        self,
        reference: str,
        entry: Mapping[str, object],
        context: PlacementContext,
    ) -> Placement | None:
        if reference != ComponentReference.HOST_GPIO_HEADER:
            return None
        return _placement(
            reference,
            entry,
            context.dimensions.PI_BAY_CENTER_MM,
            context.dimensions.PI_HEADER_ROTATION_DEG,
        )


class StripPlacementRule:
    """Place one-off power, display, and bring-up parts on the control strip."""

    def place(
        self,
        reference: str,
        entry: Mapping[str, object],
        context: PlacementContext,
    ) -> Placement | None:
        raw = context.dimensions.PCB_STRIP_PLACEMENTS_MM.get(reference)
        if raw is None:
            return None
        x, y, rotation = raw
        return _placement(reference, entry, (x, y), rotation)


class ExpanderBypassPlacementRule:
    """Place each expander's local bypass capacitor beside its owning IC."""

    def place(
        self,
        reference: str,
        entry: Mapping[str, object],
        context: PlacementContext,
    ) -> Placement | None:
        expander_reference = _extras(reference, entry).get("For")
        if entry.get("lib") != "C" or expander_reference is None:
            return None
        if not isinstance(expander_reference, str):
            raise ValueError(f"{reference}: decoupled component must be a string")
        try:
            expander = context.components[expander_reference]
        except KeyError as error:
            raise RuntimeError(
                f"{reference}: unknown decoupled component {expander_reference!r}"
            ) from error
        if expander.get("lib") != "TCA9554":
            raise RuntimeError(
                f"{reference}: decouples non-expander {expander_reference}"
            )
        bank = _extras(str(expander_reference), expander).get("Bank")
        if not isinstance(bank, str):
            raise ValueError(f"{expander_reference}: bank must be a string")
        expander_position = context.dimensions.EXPANDER_POSITIONS_BY_BANK_MM[bank]
        offset = Tca9554.BYPASS_OFFSET_MM
        position = (expander_position[0] + offset[0], expander_position[1] + offset[1])
        return _placement(reference, entry, position)


PLACEMENT_RULES: tuple[PlacementRule[PlacementContext], ...] = (
    SquarePlacementRule(),
    ExpanderPlacementRule(),
    ControlPlacementRule(),
    HostPlacementRule(),
    StripPlacementRule(),
    ExpanderBypassPlacementRule(),
)


def square_centres(shared: sources.DimensionsSource) -> dict[str, tuple[float, float]]:
    """Bridge mechanical far-side rows to electrical near-side rank names."""
    centres: dict[str, tuple[float, float]] = {}
    for row, column, x, y in shared.BOARD_SQUARE_CENTERS_MM:
        name = f"{sources.names().FILES[column]}{shared.GRID_COUNT - row}"
        centres[name] = (x, y)
    return centres


def build(netlist: Mapping[str, object] | None = None) -> list[Placement]:
    """Plan every component and reject missing or ambiguous rule ownership."""
    dimensions = sources.dimensions()
    names = sources.names()
    contract = netlist or sources.netlist()
    components = _component_entries(contract)
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
