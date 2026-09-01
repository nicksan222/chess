"""Validated, KiCad-independent electrical connection graph."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from core.placement import Placement

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
        for connection in self.connections:
            for endpoint in connection.endpoints:
                if endpoint in endpoint_nets:
                    raise ValueError(f"endpoint {endpoint} belongs to multiple nets")
                endpoint_nets[endpoint] = connection.name
        self._endpoint_nets = endpoint_nets

    @classmethod
    def from_contract(
        cls,
        serialized: Iterable[Mapping[str, object]],
        placements: Iterable[Placement],
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
            endpoints = tuple(_endpoint(value) for value in raw_endpoints)
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

    def net_name(self, endpoint: EndpointKey) -> str:
        try:
            return self._endpoint_nets[endpoint]
        except KeyError as error:
            raise KeyError(f"no connection for endpoint {endpoint}") from error

    def for_component(self, reference: str) -> tuple[Connection, ...]:
        """Return every connection touching one component instance."""
        return tuple(
            connection
            for connection in self.connections
            if connection.touches(reference)
        )


def _endpoint(value: object) -> EndpointKey:
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError(f"invalid serialized endpoint {value!r}")
    reference, pin = value
    if not isinstance(reference, str) or not isinstance(pin, str):
        raise ValueError(f"endpoint values must be strings: {value!r}")
    return reference, pin
