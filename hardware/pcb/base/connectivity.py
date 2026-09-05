"""Validated, KiCad-independent electrical connection graph."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from typing import TypeGuard

from base.component import BoundPin, Endpoint, EndpointResolver
from base.placement import Placement

EndpointKey = tuple[str, str]


@dataclass(frozen=True)
class Connection:
    """One named electrical net or one deliberate no-connect endpoint."""

    name: str
    endpoints: tuple[EndpointKey, ...]
    no_connect: bool = False

    def __post_init__(self) -> None:
        if not self.endpoints:
            raise ValueError("a connection needs at least one endpoint")
        if self.no_connect and len(self.endpoints) != 1:
            raise ValueError("a no-connect group must contain exactly one endpoint")
        if len(set(self.endpoints)) != len(self.endpoints):
            raise ValueError("an endpoint belongs to multiple nets or is repeated")

    @classmethod
    def from_pins(
        cls, name: str, *pins: BoundPin, no_connect: bool = False
    ) -> Connection:
        """Define an electrical group using bound component pins, not pad strings."""
        return cls(name, tuple(pin.endpoint for pin in pins), no_connect)

    def touches(self, reference: str) -> bool:
        return any(endpoint[0] == reference for endpoint in self.endpoints)


class ConnectionGraph:
    """Indexed electrical contract consumed by schematic and PCB adapters."""

    def __init__(self, connections: Iterable[Connection]) -> None:
        self.connections = tuple(connections)
        endpoint_nets: dict[EndpointKey, str] = {}
        endpoint_connections: dict[EndpointKey, Connection] = {}
        names: set[str] = set()
        for connection in self.connections:
            if connection.name in names:
                raise ValueError(f"duplicate connection name {connection.name!r}")
            names.add(connection.name)
            for endpoint in connection.endpoints:
                if endpoint in endpoint_nets:
                    raise ValueError(f"endpoint {endpoint} belongs to multiple nets")
                endpoint_nets[endpoint] = connection.name
                endpoint_connections[endpoint] = connection
        self._endpoint_nets = endpoint_nets
        self._endpoint_connections = endpoint_connections
        self._connections_by_name = {
            connection.name: connection for connection in self.connections
        }

    @classmethod
    def from_contract(
        cls,
        serialized: Iterable[Mapping[str, object]],
        placements: Iterable[Placement],
        components: Mapping[str, EndpointResolver] | None = None,
    ) -> ConnectionGraph:
        """Resolve serialized logical pins, including KiCad no-connect net names."""
        from base.connection_contract import ConnectionContract

        return ConnectionContract(placements, components).build(
            serialized, graph_type=cls
        )

    @property
    def names(self) -> tuple[str, ...]:
        """Return deterministic unique net names."""
        return tuple(sorted({connection.name for connection in self.connections}))

    def named(self, name: str) -> Connection:
        """Resolve a subsystem's net without rebuilding a separate wiring map."""
        try:
            return self._connections_by_name[name]
        except KeyError as error:
            raise KeyError(f"no connection named {name!r}") from error

    def connection_for(self, endpoint: EndpointKey) -> Connection:
        """Return the complete connection containing ``endpoint``."""
        try:
            return self._endpoint_connections[endpoint]
        except KeyError as error:
            raise KeyError(f"no connection for endpoint {endpoint}") from error

    def net_name(self, endpoint: EndpointKey) -> str:
        try:
            return self._endpoint_nets[endpoint]
        except KeyError as error:
            raise KeyError(f"no connection for endpoint {endpoint}") from error

    def peers(self, endpoint: EndpointKey) -> tuple[Endpoint[str], ...]:
        """Return typed endpoints electrically attached to ``endpoint``."""
        return tuple(
            Endpoint(reference, pin)
            for reference, pin in self.connection_for(endpoint).endpoints
            if (reference, pin) != endpoint
        )

    def for_component(self, reference: str) -> tuple[Connection, ...]:
        """Return every connection touching one component instance."""
        return tuple(
            connection
            for connection in self.connections
            if connection.touches(reference)
        )


class CircuitBuilder:
    """Readable, checked API for composing a connection graph from typed pins."""

    def __init__(self) -> None:
        self._connections: list[Connection] = []
        self._attached: set[EndpointKey] = set()

    def connect(
        self,
        *pins: BoundPin,
        name: str | None = None,
        no_connect: bool = False,
    ) -> CircuitBuilder:
        if not pins:
            raise ValueError("a connection needs at least one pin")
        if no_connect and len(pins) != 1:
            raise ValueError("a no-connect group must contain exactly one pin")
        connection_name = name or f"N${len(self._connections) + 1}"
        return self.add(
            Connection.from_pins(connection_name, *pins, no_connect=no_connect)
        )

    def add(self, connection: Connection) -> CircuitBuilder:
        """Attach an object definition atomically; a pin has exactly one owner.

        Name collisions are checked by ``build`` as before. Failed endpoint
        validation leaves the builder unchanged so callers can correct a group.
        """
        duplicate = self._attached.intersection(connection.endpoints)
        if duplicate:
            raise ValueError(f"pins already attached: {sorted(duplicate)}")
        self._connections.append(connection)
        self._attached.update(connection.endpoints)
        return self

    def no_connect(self, pin: BoundPin) -> CircuitBuilder:
        return self.connect(pin, name=f"NC:{pin.endpoint!s}", no_connect=True)

    def build(self) -> ConnectionGraph:
        return ConnectionGraph(self._connections)


def typed_endpoint(
    value: object,
    components: Mapping[str, EndpointResolver],
) -> Endpoint[str]:
    """Resolve one serialized endpoint to its component's semantic pin enum."""
    reference, number = serialized_endpoint(value)
    try:
        component = components[reference]
    except KeyError as error:
        raise ValueError(f"unknown component {reference!r}") from error
    return component.resolve_endpoint(number)


def is_object_list(value: object) -> TypeGuard[list[object]]:
    """Narrow JSON arrays without treating their unchecked elements as Any."""
    return isinstance(value, list)


def serialized_endpoint(value: object) -> EndpointKey:
    """Validate the two string fields before component-specific pin resolution."""
    if not is_object_list(value) or len(value) != 2:
        raise ValueError(f"invalid serialized endpoint {value!r}")
    reference, pin = value
    if not isinstance(reference, str) or not isinstance(pin, str):
        raise ValueError(f"endpoint values must be strings: {value!r}")
    return reference, pin
