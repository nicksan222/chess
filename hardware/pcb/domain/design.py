"""Reusable typed aggregate shared by PCB output adapters."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from domain.component import BoundPin, EndpointResolver
from domain.connectivity import ConnectionGraph
from domain.placement import Placement
from domain.validation import is_string_mapping


@dataclass(frozen=True)
class ComponentSpec:
    """Reviewed product and design metadata for one component instance."""

    reference: str
    part_key: str
    package: str
    library: str
    value: str
    description: str
    extras: Mapping[str, object]

    @classmethod
    def from_contract(
        cls,
        reference: str,
        entry: Mapping[str, object],
    ) -> ComponentSpec:
        def text(key: str) -> str:
            value = entry.get(key)
            if not isinstance(value, str):
                raise ValueError(f"{reference}: component {key} must be a string")
            return value

        extras = entry.get("extras")
        if not is_string_mapping(extras):
            raise ValueError(f"{reference}: component extras must have string keys")
        return cls(
            reference=reference,
            part_key=text("part_key"),
            package=text("package"),
            library=text("lib"),
            value=text("value"),
            description=text("description"),
            extras=MappingProxyType(dict(extras)),
        )


@dataclass(frozen=True)
class ComponentInstance:
    """One product, its typed pinout, metadata, and physical placement."""

    spec: ComponentSpec
    model: EndpointResolver
    placement: Placement

    @property
    def reference(self) -> str:
        return self.spec.reference

    def model_as[Model: EndpointResolver](self, model_type: type[Model]) -> Model:
        """Require a specific product before using its semantic pin operations.

        The board aggregate holds heterogeneous models. Routing should narrow a
        model through this checked accessor, never cast it to a convenient type.
        """
        if not isinstance(self.model, model_type):
            raise ValueError(f"{self.reference}: expected {model_type.__name__}")
        return self.model

    @property
    def pins(self) -> tuple[BoundPin, ...]:
        return self.model.pins


@dataclass(frozen=True)
class BoardDesign:
    """Fully validated object graph consumed by every output adapter."""

    title: str
    revision: str
    components: Mapping[str, ComponentInstance]
    connections: ConnectionGraph
    placements: tuple[Placement, ...]

    @classmethod
    def create(
        cls,
        *,
        title: str,
        revision: str,
        components: Mapping[str, ComponentInstance],
        connections: ConnectionGraph,
        placements: tuple[Placement, ...],
    ) -> BoardDesign:
        return cls(
            title,
            revision,
            MappingProxyType(dict(components)),
            connections,
            placements,
        )

    def component(self, reference: str) -> ComponentInstance:
        try:
            return self.components[reference]
        except KeyError as error:
            raise KeyError(f"board has no component {reference!r}") from error

    def pin(self, reference: str, number: str) -> BoundPin:
        """Resolve a serialized number through the owning component boundary."""
        return self.component(reference).model.bind_pin(number)
