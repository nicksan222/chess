"""Reusable placement values and checked rule coordination."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from base.footprint import Footprint

if TYPE_CHECKING:
    from base.kicad.board import KiCadBoard


@dataclass(frozen=True)
class Placement:
    """One packaged component positioned and oriented in board coordinates."""

    reference: str
    package: str
    x: float
    y: float
    rotation: float
    footprint: Footprint

    def pads(self):
        """Yield logical/physical pads and definitions in board coordinates."""
        for pad in self.footprint.pads:
            turned = pad.rotated(self.rotation)
            yield (
                pad.net_number,
                pad.number,
                (round(self.x + turned.x, 4), round(self.y + turned.y, 4)),
                turned,
            )

    def attach_to(
        self,
        board: KiCadBoard,
        component_entry: Mapping[str, object],
    ) -> None:
        """Compatibility helper for callers holding a raw component contract."""
        board.attach_component(self, component_entry)

    def courtyard(self) -> tuple[float, float, float, float]:
        """Bounding box as ``(x_min, y_min, x_max, y_max)``."""
        width, height = self.footprint.courtyard_at(self.rotation)
        return (
            self.x - width / 2.0,
            self.y - height / 2.0,
            self.x + width / 2.0,
            self.y + height / 2.0,
        )


class PlacementRule[Context](Protocol):
    """One design feature's ownership of component positioning."""

    def place(
        self,
        reference: str,
        entry: Mapping[str, object],
        context: Context,
    ) -> Placement | None: ...


@dataclass(frozen=True)
class PlacementPlanner[Context]:
    """Apply focused rules and reject missing or ambiguous ownership."""

    rules: tuple[PlacementRule[Context], ...]

    def plan(
        self,
        components: Mapping[str, Mapping[str, object]],
        context: Context,
    ) -> list[Placement]:
        placements = []
        for reference, entry in sorted(components.items()):
            matches = [
                result
                for rule in self.rules
                if (result := rule.place(reference, entry, context)) is not None
            ]
            if not matches:
                raise RuntimeError(
                    f"{reference} ({entry['lib']}, {entry['package']}) "
                    "has no placement rule"
                )
            if len(matches) > 1:
                raise RuntimeError(f"{reference} is owned by multiple placement rules")
            placements.append(matches[0])
        return placements
