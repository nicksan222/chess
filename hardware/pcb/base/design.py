"""Reusable typed aggregate shared by PCB output adapters."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from types import MappingProxyType

from base.component import BoardComponent, ComponentPin
from base.connectivity import ConnectionGraph
from base.placement import Placement


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
        if not isinstance(extras, Mapping):
            raise ValueError(f"{reference}: component extras must be a mapping")
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
    model: BoardComponent
    placement: Placement

    @property
    def reference(self) -> str:
        return self.spec.reference

    @property
    def pins(self) -> tuple[ComponentPin, ...]:
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

    def pin(self, reference: str, number: str) -> ComponentPin:
        """Resolve a serialized datasheet number to a capable typed pin object."""
        component = self.component(reference).model
        return component.pin(component.get_pin_by_number(number))
