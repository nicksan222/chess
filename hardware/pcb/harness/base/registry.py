"""Collect component and scenario declarations into one board design."""

from __future__ import annotations

from enum import StrEnum
from typing import cast

from .component import BoardComponent, RegisteredComponent
from .connections import Endpoint, NetConnection, NoConnect
from .geometry import courtyards_overlap
from .net import Net
from .pcbnew.outline import BoardOutline
from .spice.analysis import AcSweep
from .spice.measurement import (
    CurrentThrough,
    SpiceRequirement,
    VoltageAt,
    VoltageBetween,
)
from .spice.scenario import SpiceScenario
from .spice.source import CurrentSource, VoltageSource


class BoardRegistry:
    """The explicit destination for auto-registered components and scenarios.

    Pass this registry to every component and scenario constructor. The
    constructors register themselves after local validation. Supplying a board
    outline also checks each new component's courtyard against the edge and
    all existing components before storing it. Registration rejects
    conflicting facts for placements of the same purchased part. ``validate``
    repeats those checks and resolves forward references to real pins, shared
    nets and simulation sources. ``net_members`` reports declared topology, not
    routed copper. The registry is the typed intent layer; KiCad DRC and SPICE
    still check the resulting physical and electrical behavior separately.
    """

    def __init__(self, *, outline: BoardOutline | None = None) -> None:
        """Begin an empty board; an outline enables immediate physical checks."""
        if outline is not None and not isinstance(cast(object, outline), BoardOutline):
            raise ValueError("registry outline must be a BoardOutline")
        self._physical_outline = outline
        self._components: dict[str, RegisteredComponent] = {}
        self._scenarios: dict[str, SpiceScenario] = {}
        self._requirements: list[tuple[str, SpiceRequirement]] = []

    def register_component(self, component: RegisteredComponent) -> None:
        """Reject duplicate references and impossible placements before storing."""
        if component.reference in self._components:
            raise ValueError(f"duplicate component reference: {component.reference}")
        self._check_product_consistency(component, tuple(self._components.values()))
        if self._physical_outline is not None:
            self._check_physical_component(
                component, tuple(self._components.values()), self._physical_outline
            )
        self._components[component.reference] = component

    @staticmethod
    def _check_product_consistency(
        component: RegisteredComponent, previous: tuple[RegisteredComponent, ...]
    ) -> None:
        """Prevent one maker part number from gaining contradictory facts."""
        if not isinstance(component, BoardComponent):
            return
        part = cast(BoardComponent[StrEnum], component)
        product = part.definition.product
        for other in previous:
            if not isinstance(other, BoardComponent):
                continue
            prior = cast(BoardComponent[StrEnum], other)
            known = prior.definition.product
            if (known.manufacturer, known.part_number) != (
                product.manufacturer,
                product.part_number,
            ):
                continue
            if (
                type(part) is not type(prior)
                or part.definition != prior.definition
                or part.product_parameters() != prior.product_parameters()
            ):
                raise ValueError(
                    f"{other.reference} and {component.reference}: "
                    f"inconsistent product facts for "
                    f"{product.manufacturer} {product.part_number}"
                )

    @staticmethod
    def _check_physical_component(
        component: RegisteredComponent,
        previous: tuple[RegisteredComponent, ...],
        outline: BoardOutline,
    ) -> None:
        """Check one complete placement against board edges and earlier parts."""
        if not isinstance(component, BoardComponent):
            raise ValueError("physical registry needs BoardComponent instances")
        part = cast(BoardComponent[StrEnum], component)
        if not outline.contains(part.placement, part.definition.courtyard):
            raise ValueError(f"{part.reference}: courtyard exceeds board outline")
        for other in previous:
            if not isinstance(other, BoardComponent):
                raise ValueError("physical registry needs BoardComponent instances")
            prior = cast(BoardComponent[StrEnum], other)
            if courtyards_overlap(
                prior.placement,
                prior.definition.courtyard,
                part.placement,
                part.definition.courtyard,
            ):
                raise ValueError(
                    f"{prior.reference} and {part.reference}: courtyard overlap"
                )

    def validate_physical(self, outline: BoardOutline | None = None) -> None:
        """Recheck every registered placement, including rotated clearances.

        Registration checks each new part immediately when the registry has an
        outline. This full pass also protects conversion if a declaration was
        changed after registration. It tests assembly courtyards and the board
        edge; KiCad DRC remains responsible for copper and fabrication rules.
        """
        boundary = outline if outline is not None else self._physical_outline
        if boundary is None:
            raise ValueError("physical validation needs a board outline")
        if not isinstance(cast(object, boundary), BoardOutline):
            raise ValueError("physical validation needs a BoardOutline")
        previous: list[RegisteredComponent] = []
        for component in self.components():
            self._check_physical_component(component, tuple(previous), boundary)
            previous.append(component)

    def register_scenario(self, scenario: SpiceScenario) -> None:
        """Give an initialized simulation setup one unique scenario name."""
        if scenario.name in self._scenarios:
            raise ValueError(f"duplicate SPICE scenario: {scenario.name}")
        self._scenarios[scenario.name] = scenario

    def register_requirement(
        self, reference: str, requirement: SpiceRequirement
    ) -> None:
        """Attach a builder-authored proof request to an existing component."""
        if reference not in self._components:
            raise ValueError(f"unknown component reference: {reference}")
        self._requirements.append((reference, requirement))

    def register_board_requirement(self, requirement: SpiceRequirement) -> None:
        """Store a check of the whole circuit, such as total supply current."""
        self._requirements.append(("BOARD", requirement))

    def net_members(self, name: Net) -> tuple[Endpoint, ...]:
        """Derive intended members of a net from the component pin maps."""
        if not isinstance(cast(object, name), Net):
            raise ValueError("net lookup needs a Net enum member")
        return tuple(
            sorted(
                endpoint
                for component in self._components.values()
                for endpoint, connection in component.pin_connections()
                if isinstance(connection, NetConnection) and connection.net == name
            )
        )

    def components(self) -> tuple[RegisteredComponent, ...]:
        """Return every component in stable reference order for a board engine."""
        return tuple(component for _, component in sorted(self._components.items()))

    def scenario(self, name: str) -> SpiceScenario:
        """Find one declared simulation setup by its stable name."""
        try:
            return self._scenarios[name]
        except KeyError as error:
            raise ValueError(f"unknown SPICE scenario: {name}") from error

    def spice_requirements(self) -> tuple[tuple[str, SpiceRequirement], ...]:
        """Gather component and whole-board checks for circuit conversion."""
        component_requirements = tuple(
            (reference, requirement)
            for reference, component in sorted(self._components.items())
            for requirement in component.spice
        )
        return component_requirements + tuple(self._requirements)

    def validate(self) -> None:
        """Resolve exact peers, simulation setups, sources and measured points.

        Physical registries also recheck all courtyard and board-edge
        placements. KiCad DRC must separately verify copper clearance and
        connectivity. The simulation engine evaluates electrical claims
        against actual simulated results.
        """
        if self._physical_outline is not None:
            self.validate_physical()
        previous: list[RegisteredComponent] = []
        for component in self.components():
            self._check_product_consistency(component, tuple(previous))
            previous.append(component)
        assignments = {
            endpoint: connection
            for component in self._components.values()
            for endpoint, connection in component.pin_connections()
        }
        nets = {
            connection.net
            for connection in assignments.values()
            if isinstance(connection, NetConnection)
        }
        net_types = {type(net) for net in nets}
        if len(net_types) > 1:
            raise ValueError("all board connections must use one Net enum")
        board_net_type = next(iter(net_types), None)
        for endpoint, connection in assignments.items():
            if not isinstance(connection, NetConnection):
                continue
            for peer in connection.peers:
                other = assignments.get(peer)
                if not isinstance(other, NetConnection) or other.net != connection.net:
                    raise ValueError(
                        f"{endpoint.reference}/{endpoint.pin} expects "
                        f"{peer.reference}/{peer.pin} on {connection.net.label}"
                    )
        for scenario in self._scenarios.values():
            if (
                board_net_type is not None
                and type(scenario.ground_net) is not board_net_type
            ):
                raise ValueError(
                    f"{scenario.name}: scenario must use the board's one Net enum"
                )
            if scenario.ground_net not in nets:
                raise ValueError(f"{scenario.name}: unknown ground net")
            for source in scenario.sources:
                if isinstance(source, VoltageSource):
                    used = (source.positive_net, source.negative_net)
                elif isinstance(source, CurrentSource):  # pyright: ignore[reportUnnecessaryIsInstance]
                    used = (source.from_net, source.to_net)
                else:
                    raise ValueError(f"{scenario.name}: unknown source kind")
                if any(type(net) is not board_net_type for net in used):
                    raise ValueError(
                        f"{scenario.name}/{source.name}: source must use the board's one Net enum"
                    )
                if unknown := set(used) - nets:
                    raise ValueError(
                        f"{scenario.name}/{source.name}: unknown nets {sorted(net.label for net in unknown)}"
                    )
            if isinstance(scenario.analysis, AcSweep) and not any(
                isinstance(source, VoltageSource)
                and source.ac_magnitude_volts is not None
                for source in scenario.sources
            ):
                raise ValueError(f"{scenario.name}: AC excitation is required")
        for reference, requirement in self.spice_requirements():
            scenario = self._scenarios.get(requirement.scenario)
            if scenario is None:
                raise ValueError(
                    f"{reference}: unknown SPICE scenario {requirement.scenario}"
                )
            measurement = requirement.measurement
            if isinstance(measurement, VoltageAt):
                points = (measurement.pin,)
            elif isinstance(measurement, VoltageBetween):
                points = (measurement.positive, measurement.negative)
            elif isinstance(measurement, CurrentThrough):  # pyright: ignore[reportUnnecessaryIsInstance]
                sources = {s.name: s for s in scenario.sources}
                if measurement.source not in sources:
                    raise ValueError(
                        f"{reference}: unknown source {measurement.source}"
                    )
                if not isinstance(sources[measurement.source], VoltageSource):
                    raise ValueError(
                        f"{reference}: current probe needs a voltage source"
                    )
                points = ()
            else:
                raise ValueError(f"{reference}: unknown measurement kind")
            for point in points:
                if (
                    scenario.component_references is not None
                    and point.reference not in scenario.component_references
                ):
                    raise ValueError(
                        f"{reference}: measurement is outside the selected component scope"
                    )
                if point not in assignments or isinstance(
                    assignments[point], NoConnect
                ):
                    raise ValueError(
                        f"{reference}: cannot measure unconnected {point.reference}/{point.pin}"
                    )
