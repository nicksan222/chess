"""Validated, KiCad-independent electrical connection graph."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from base.component import BoardComponent, ComponentPin, Endpoint
from base.placement import Placement

EndpointKey = tuple[str, str]


@dataclass(frozen=True)
class Connection:
    """One named electrical net or one deliberate no-connect endpoint."""

    name: str
    endpoints: tuple[EndpointKey, ...]
    no_connect: bool = False

    def touches(self, reference: str) -> bool:
        return any(endpoint[0] == reference for endpoint in self.endpoints)


class ConnectionGraph:
    """Indexed electrical contract consumed by schematic and PCB adapters."""

    def __init__(self, connections: Iterable[Connection]) -> None:
        self.connections = tuple(connections)
        endpoint_nets: dict[EndpointKey, str] = {}
        endpoint_connections: dict[EndpointKey, Connection] = {}
        for connection in self.connections:
            for endpoint in connection.endpoints:
                if endpoint in endpoint_nets:
                    raise ValueError(f"endpoint {endpoint} belongs to multiple nets")
                endpoint_nets[endpoint] = connection.name
                endpoint_connections[endpoint] = connection
        self._endpoint_nets = endpoint_nets
        self._endpoint_connections = endpoint_connections

    @classmethod
    def from_contract(
        cls,
        serialized: Iterable[Mapping[str, object]],
        placements: Iterable[Placement],
        components: Mapping[str, BoardComponent] | None = None,
    ) -> ConnectionGraph:
        """Resolve serialized logical pins, including KiCad no-connect net names."""
        placed = tuple(placements)
        physical_numbers: dict[EndpointKey, str] = {}
        expected_endpoints: set[EndpointKey] = set()
        for item in placed:
            for logical, physical, _position, _definition in item.pads():
                endpoint = (item.reference, logical)
                physical_numbers.setdefault(endpoint, physical)
                expected_endpoints.add(endpoint)

        connections = []
        for index, entry in enumerate(serialized, 1):
            raw_endpoints = entry.get("pads")
            if not isinstance(raw_endpoints, list):
                raise ValueError("connection pads must be a list")
            endpoints = tuple(
                typed_endpoint(value, components) if components else _endpoint(value)
                for value in raw_endpoints
            )
            no_connect = bool(entry.get("no_connect", False))
            if no_connect and len(endpoints) != 1:
                raise ValueError("a no-connect group must contain exactly one endpoint")

            raw_name = entry.get("name")
            if raw_name is not None and not isinstance(raw_name, str):
                raise ValueError("connection name must be a string or null")
            if no_connect:
                reference, logical = endpoints[0]
                try:
                    physical = physical_numbers[(reference, logical)]
                except KeyError as error:
                    raise ValueError(
                        f"unknown endpoint {(reference, logical)}"
                    ) from error
                name = f"unconnected-({reference}-Pad{physical})"
            else:
                name = raw_name or f"N${index}"
            connections.append(Connection(name, endpoints, no_connect))

        graph = cls(connections)
        actual_endpoints = set(graph._endpoint_nets)
        unknown = actual_endpoints - expected_endpoints
        missing = expected_endpoints - actual_endpoints
        if unknown:
            raise ValueError(
                f"connections contain unknown endpoints: {sorted(unknown)}"
            )
        if missing:
            raise ValueError(f"component endpoints lack connections: {sorted(missing)}")
        return graph

    @property
    def names(self) -> tuple[str, ...]:
        """Return deterministic unique net names."""
        return tuple(sorted({connection.name for connection in self.connections}))

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

    def peers(self, endpoint: EndpointKey) -> tuple[Endpoint, ...]:
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
        *pins: ComponentPin,
        name: str | None = None,
        no_connect: bool = False,
    ) -> CircuitBuilder:
        if not pins:
            raise ValueError("a connection needs at least one pin")
        if no_connect and len(pins) != 1:
            raise ValueError("a no-connect group must contain exactly one pin")
        endpoints = tuple(pin.endpoint for pin in pins)
        duplicate = self._attached.intersection(endpoints)
        if duplicate:
            raise ValueError(f"pins already attached: {sorted(duplicate)}")
        connection_name = name or f"N${len(self._connections) + 1}"
        self._connections.append(Connection(connection_name, endpoints, no_connect))
        self._attached.update(endpoints)
        return self

    def no_connect(self, pin: ComponentPin) -> CircuitBuilder:
        return self.connect(pin, name=f"NC:{pin.endpoint!s}", no_connect=True)

    def build(self) -> ConnectionGraph:
        return ConnectionGraph(self._connections)


def typed_endpoint(
    value: object,
    components: Mapping[str, BoardComponent],
) -> Endpoint:
    """Resolve one serialized endpoint to its component's semantic pin enum."""
    reference, number = _endpoint(value)
    try:
        component = components[reference]
    except KeyError as error:
        raise ValueError(f"unknown component {reference!r}") from error
    return component.endpoint(component.get_pin_by_number(number))


def _endpoint(value: object) -> EndpointKey:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"invalid serialized endpoint {value!r}")
    reference, pin = value
    if not isinstance(reference, str) or not isinstance(pin, str):
        raise ValueError(f"endpoint values must be strings: {value!r}")
    return reference, pin
