"""Named mechanical instances and automatic declaration checks."""

from typing import TypeVar

from .component import Component, PrintableComponent

Part = TypeVar("Part", bound=Component)


class ModelRegistry:
    def __init__(self) -> None:
        self._components: dict[str, Component] = {}

    def add(self, part: Part) -> Part:
        if part.reference in self._components:
            raise ValueError(f"duplicate component: {part.reference}")
        existing = {name for known in self.components() for name in known.object_names}
        if len(set(part.object_names)) != len(
            part.object_names
        ) or existing.intersection(part.object_names):
            raise ValueError("component object names must be unique")
        self._components[part.reference] = part
        return part

    def components(self) -> tuple[Component, ...]:
        return tuple(self._components.values())

    def printable_components(self) -> tuple[PrintableComponent, ...]:
        return tuple(
            part for part in self.components() if isinstance(part, PrintableComponent)
        )

    def validate(self) -> None:
        if not self.components():
            raise ValueError("model needs components")
        outputs = [part.output_name for part in self.printable_components()]
        if (
            not outputs
            or any(not name for name in outputs)
            or len(set(outputs)) != len(outputs)
        ):
            raise ValueError("printable components need unique output names")
