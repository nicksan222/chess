"""Reusable physical composition of one illuminated, sensed chessboard square.

This module deliberately has no KiCad dependency. A square can therefore be
validated as a small product unit before the 64 instances are placed or routed.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum

from shared import dimensions as shared


class SquareRole(StrEnum):
    LED = "LED"
    HALL_SENSOR = "Hall sensor"
    LED_BYPASS = "LED bypass capacitor"
    HALL_BYPASS = "Hall bypass capacitor"


@dataclass(frozen=True)
class SquarePart:
    """Identity and package of one part belonging to a square."""

    reference: str
    package: str


@dataclass(frozen=True)
class SquarePartPlacement:
    """Absolute placement produced by a composed square."""

    reference: str
    package: str
    x: float
    y: float
    rotation: float = 0.0


@dataclass(frozen=True)
class SquareAssembly:
    """The four physical parts repeated once at every board square."""

    name: str
    centre: tuple[float, float]
    led_offset: tuple[float, float]
    led: SquarePart
    hall_sensor: SquarePart
    led_bypass: SquarePart
    hall_bypass: SquarePart

    @classmethod
    def from_components(
        cls,
        name: str,
        centre: tuple[float, float],
        led_offset: tuple[float, float],
        components: Mapping[str, Mapping[str, object]],
    ) -> SquareAssembly:
        """Compose one square from reviewed component-contract entries."""
        members = {
            reference: entry
            for reference, entry in components.items()
            if _extras(entry).get("Square") == name
        }

        def select(
            role: SquareRole,
            predicate: Callable[[Mapping[str, object]], bool],
        ) -> SquarePart:
            matches = [
                SquarePart(reference, _string(entry, "package"))
                for reference, entry in members.items()
                if predicate(entry)
            ]
            if len(matches) != 1:
                raise ValueError(
                    f"square {name} needs exactly one {role}; found {len(matches)}"
                )
            return matches[0]

        led = select(
            SquareRole.LED,
            lambda entry: entry.get("part_key") == "SK9822",
        )
        hall_sensor = select(
            SquareRole.HALL_SENSOR,
            lambda entry: entry.get("part_key") == "HALL_SENSOR",
        )
        hall_bypass = select(
            SquareRole.HALL_BYPASS,
            lambda entry: (
                entry.get("part_key") == "CAP_100N" and "Sensor" in _extras(entry)
            ),
        )
        led_bypass = select(
            SquareRole.LED_BYPASS,
            lambda entry: (
                entry.get("part_key") == "CAP_100N" and "Sensor" not in _extras(entry)
            ),
        )

        selected_references = {
            led.reference,
            hall_sensor.reference,
            led_bypass.reference,
            hall_bypass.reference,
        }
        unexpected = set(members) - selected_references
        if unexpected:
            raise ValueError(
                f"square {name} has unexpected components: {sorted(unexpected)}"
            )

        hall_cap_entry = members[hall_bypass.reference]
        sensor_reference = _extras(hall_cap_entry).get("Sensor")
        if sensor_reference != hall_sensor.reference:
            raise ValueError(
                f"square {name} Hall bypass names {sensor_reference!r}, "
                f"not {hall_sensor.reference}"
            )

        return cls(
            name,
            centre,
            led_offset,
            led,
            hall_sensor,
            led_bypass,
            hall_bypass,
        )

    def placements(self) -> tuple[SquarePartPlacement, ...]:
        """Place the four parts while preserving the serpentine LED chain."""
        x, y = self.centre
        led_x = x + self.led_offset[0]
        led_y = y + self.led_offset[1]
        led_rotation = 180.0 if _rank(self.name) % 2 == 0 else 0.0
        return (
            SquarePartPlacement(
                self.led.reference,
                self.led.package,
                led_x,
                led_y,
                led_rotation,
            ),
            SquarePartPlacement(
                self.hall_sensor.reference,
                self.hall_sensor.package,
                x,
                y,
            ),
            SquarePartPlacement(
                self.led_bypass.reference,
                self.led_bypass.package,
                led_x + shared.LED_BYPASS_OFFSET_MM[0],
                led_y + shared.LED_BYPASS_OFFSET_MM[1],
            ),
            SquarePartPlacement(
                self.hall_bypass.reference,
                self.hall_bypass.package,
                x + shared.HALL_BYPASS_OFFSET_MM[0],
                y + shared.HALL_BYPASS_OFFSET_MM[1],
            ),
        )


def build_all(
    components: Mapping[str, Mapping[str, object]],
    centres: Mapping[str, tuple[float, float]],
    led_offset: tuple[float, float],
) -> tuple[SquareAssembly, ...]:
    """Build every expected square and reject component references to unknown ones."""
    named_squares: set[str] = set()
    for entry in components.values():
        square_name = _extras(entry).get("Square")
        if square_name is None:
            continue
        if not isinstance(square_name, str):
            raise ValueError("component Square metadata must be a string")
        named_squares.add(square_name)
    unknown = named_squares - set(centres)
    if unknown:
        raise ValueError(f"components name unknown squares: {sorted(unknown)}")
    return tuple(
        SquareAssembly.from_components(name, centre, led_offset, components)
        for name, centre in sorted(centres.items())
    )


def _extras(entry: Mapping[str, object]) -> Mapping[str, object]:
    extras = entry.get("extras")
    if not isinstance(extras, Mapping):
        raise ValueError("component extras must be a mapping")
    return extras


def _string(entry: Mapping[str, object], key: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str):
        raise ValueError(f"component {key} must be a string")
    return value


def _rank(name: str) -> int:
    if len(name) != 2 or name[0] not in "ABCDEFGH" or name[1] not in "12345678":
        raise ValueError(f"invalid square name {name!r}")
    return int(name[1])
