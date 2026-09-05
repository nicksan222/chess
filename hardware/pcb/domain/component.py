"""Compatibility exports for shared electronic component behavior.

Electronic identity and connection behavior belong to ``hardware/shared`` so CAD,
firmware tooling, and PCB generation use one typed model.  Existing PCB imports
remain stable through this intentionally thin boundary.
"""

from typing import Protocol

from domain.footprint import Footprint
from shared.electronics import (
    BoundPin,
    ComponentPin,
    ComponentReference,
    ConnectionSink,
    ElectronicComponent,
    Endpoint,
    EndpointResolver,
    NetLookup,
)

BoardComponent = ElectronicComponent


class PcbComponent(EndpointResolver, Protocol):
    """Heterogeneous component view required by PCB placement."""

    @classmethod
    def supports_part_key(cls, part_key: str) -> bool: ...

    def footprint_for(self, package: str) -> Footprint: ...


__all__ = (
    "BoardComponent",
    "BoundPin",
    "ComponentPin",
    "ComponentReference",
    "ConnectionSink",
    "Endpoint",
    "EndpointResolver",
    "NetLookup",
    "PcbComponent",
)
