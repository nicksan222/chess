"""Stable physical, electrical, and routing identities for panel buttons."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

Point = tuple[float, float]


@dataclass(frozen=True, slots=True)
class PanelButton:
    name: str
    gpio: int
    position_mm: Point
    switch_reference: str
    routing_priority: int
    header_launch_x_offset_mm: float
    fallback_layer_index: int

    @property
    def net_name(self) -> str:
        return f"BTN_{self.name}"

    @property
    def x_mm(self) -> float:
        return self.position_mm[0]

    @property
    def y_mm(self) -> float:
        return self.position_mm[1]


@dataclass(frozen=True, slots=True)
class PanelLayout:
    buttons: tuple[PanelButton, ...]

    def __iter__(self) -> Iterator[PanelButton]:
        return iter(self.buttons)

    def __len__(self) -> int:
        return len(self.buttons)

    def by_name(self, name: str) -> PanelButton:
        try:
            return next(button for button in self if button.name == name)
        except StopIteration as error:
            raise KeyError(name) from error

    @property
    def routing_order(self) -> tuple[PanelButton, ...]:
        return tuple(sorted(self, key=lambda button: button.routing_priority))

    def validate(self) -> None:
        if len(self) != 12:
            raise ValueError("Control panel must contain twelve buttons")
        for values, label in (
            ({button.name for button in self}, "names"),
            ({button.gpio for button in self}, "GPIOs"),
            ({button.position_mm for button in self}, "positions"),
            ({button.switch_reference for button in self}, "switch references"),
        ):
            if len(values) != len(self):
                raise ValueError(f"Panel button {label} must be unique")
        if {button.routing_priority for button in self} != set(range(len(self))):
            raise ValueError("Panel button routing priorities must be contiguous")
        if any(button.fallback_layer_index not in range(3) for button in self):
            raise ValueError("Panel fallback layer indices must select layers 0-2")


PANEL_BUTTONS = PanelLayout(
    (
        PanelButton("UP", 5, (0.0, -172.0), "SW1", 11, 0.8, 2),
        PanelButton("DOWN", 6, (16.0, -172.0), "SW2", 10, -0.8, 1),
        PanelButton("LEFT", 12, (32.0, -172.0), "SW3", 9, 0.8, 0),
        PanelButton("RIGHT", 13, (48.0, -172.0), "SW4", 8, -0.8, 2),
        PanelButton("OK", 16, (64.0, -172.0), "SW5", 7, 0.8, 1),
        PanelButton("RESET", 17, (80.0, -172.0), "SW6", 3, 0.8, 0),
        PanelButton("PASS", 19, (0.0, -188.0), "SW7", 4, -0.8, 1),
        PanelButton("F1", 20, (16.0, -188.0), "SW8", 5, 0.8, 0),
        PanelButton("F2", 21, (32.0, -188.0), "SW9", 6, -0.8, 0),
        PanelButton("F3", 22, (48.0, -188.0), "SW10", 0, 0.8, 2),
        PanelButton("F4", 23, (64.0, -188.0), "SW11", 1, 0.8, 1),
        PanelButton("F5", 24, (80.0, -188.0), "SW12", 2, -0.8, 2),
    )
)
PANEL_BUTTONS.validate()
