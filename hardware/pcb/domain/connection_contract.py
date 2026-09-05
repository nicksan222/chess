"""Deserialize the reviewed netlist into objects; this is the electrical truth boundary."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

from domain.component import EndpointResolver
from domain.connectivity import (
    Connection,
    ConnectionGraph,
    EndpointKey,
    is_object_list,
    serialized_endpoint,
    typed_endpoint,
)
from domain.placement import Placement


class ConnectionContract:
    """Resolve logical pins and enforce complete placement coverage.

    Physical pad aliases collapse to one logical endpoint. No-connect names still
    use the first physical pad number, as required by KiCad serialization.
    """

    def __init__(
        self,
        placements: Iterable[Placement],
        components: Mapping[str, EndpointResolver] | None = None,
    ) -> None:
        physical_numbers: dict[EndpointKey, str] = {}
        expected_endpoints: set[EndpointKey] = set()
        for item in placements:
            for logical, physical, _position, _definition in item.pads():
                endpoint = (item.reference, logical)
                physical_numbers.setdefault(endpoint, physical)
                expected_endpoints.add(endpoint)

        self.physical_numbers = physical_numbers
        self.expected_endpoints = expected_endpoints
        self.components = components

    def build(
        self,
        serialized: Iterable[Mapping[str, object]],
        *,
        graph_type: type[ConnectionGraph] = ConnectionGraph,
    ) -> ConnectionGraph:
        """Build once from authoritative connections, never the derived nets field."""
        connections: list[Connection] = []
        for index, entry in enumerate(serialized, 1):
            raw_endpoints = entry.get("pads")
            if not is_object_list(raw_endpoints):
                raise ValueError("connection pads must be a list")
            endpoints = tuple(
                typed_endpoint(value, self.components)
                if self.components is not None
                else serialized_endpoint(value)
                for value in raw_endpoints
            )
            no_connect = entry.get("no_connect", False)
            if not isinstance(no_connect, bool):
                raise ValueError("connection no_connect must be a boolean")
            if no_connect and len(endpoints) != 1:
                raise ValueError("a no-connect group must contain exactly one endpoint")

            raw_name = entry.get("name")
            if raw_name is not None and not isinstance(raw_name, str):
                raise ValueError("connection name must be a string or null")
            if no_connect:
                reference, logical = endpoints[0]
                try:
                    physical = self.physical_numbers[(reference, logical)]
                except KeyError as error:
                    raise ValueError(
                        f"unknown endpoint {(reference, logical)}"
                    ) from error
                name = f"unconnected-({reference}-Pad{physical})"
            else:
                name = raw_name or f"N${index}"
            connections.append(Connection(name, endpoints, no_connect))

        graph = graph_type(connections)
        actual_endpoints = {
            endpoint
            for connection in graph.connections
            for endpoint in connection.endpoints
        }
        unknown = actual_endpoints - self.expected_endpoints
        missing = self.expected_endpoints - actual_endpoints
        if unknown:
            raise ValueError(
                f"connections contain unknown endpoints: {sorted(unknown)}"
            )
        if missing:
            raise ValueError(f"component endpoints lack connections: {sorted(missing)}")
        return graph
