"""Stable physical, electrical, and routing identities for panel buttons.

Role: the one table describing the twelve front-panel buttons: where each switch
sits on the board, which Pi header pin/GPIO it is wired to, and the hints the
router uses to escape each button's net. The PCB controls assembly, routing
policies and `wiring.py` (GPIO list) read it; firmware button mapping is
hand-maintained and must match the GPIO numbers derived here.
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from shared.electronics.raspberry_pi_header import RaspberryPiHeaderPin

# (x, y) in board millimetres, origin at the playing-area centre, Y up.
Point = tuple[float, float]


@dataclass(frozen=True, slots=True)
class PanelButton:
    name: str
    position_mm: Point
    switch_reference: str
    routing_priority: int
    header_launch_x_offset_mm: float
    fallback_layer_index: int
    header_pin: RaspberryPiHeaderPin

    @property
    def gpio(self) -> int:
        return int(self.header_pin.name.rsplit("GPIO", maxsplit=1)[1])

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
            ({button.header_pin for button in self}, "header pins"),
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
        PanelButton(
            name="UP",
            position_mm=(0.0, -172.0),
            switch_reference="SW1",
            routing_priority=11,
            header_launch_x_offset_mm=0.8,
            fallback_layer_index=2,
            header_pin=RaspberryPiHeaderPin.BUTTON_UP_GPIO5,
        ),
        PanelButton(
            name="DOWN",
            position_mm=(16.0, -172.0),
            switch_reference="SW2",
            routing_priority=10,
            header_launch_x_offset_mm=-0.8,
            fallback_layer_index=1,
            header_pin=RaspberryPiHeaderPin.BUTTON_DOWN_GPIO6,
        ),
        PanelButton(
            name="LEFT",
            position_mm=(32.0, -172.0),
            switch_reference="SW3",
            routing_priority=9,
            header_launch_x_offset_mm=0.8,
            fallback_layer_index=0,
            header_pin=RaspberryPiHeaderPin.BUTTON_LEFT_GPIO12,
        ),
        PanelButton(
            name="RIGHT",
            position_mm=(48.0, -172.0),
            switch_reference="SW4",
            routing_priority=8,
            header_launch_x_offset_mm=-0.8,
            fallback_layer_index=2,
            header_pin=RaspberryPiHeaderPin.BUTTON_RIGHT_GPIO13,
        ),
        PanelButton(
            name="OK",
            position_mm=(64.0, -172.0),
            switch_reference="SW5",
            routing_priority=7,
            header_launch_x_offset_mm=0.8,
            fallback_layer_index=1,
            header_pin=RaspberryPiHeaderPin.BUTTON_OK_GPIO16,
        ),
        PanelButton(
            name="RESET",
            position_mm=(80.0, -172.0),
            switch_reference="SW6",
            routing_priority=3,
            header_launch_x_offset_mm=0.8,
            fallback_layer_index=0,
            header_pin=RaspberryPiHeaderPin.BUTTON_RESET_GPIO17,
        ),
        PanelButton(
            name="PASS",
            position_mm=(0.0, -188.0),
            switch_reference="SW7",
            routing_priority=4,
            header_launch_x_offset_mm=-0.8,
            fallback_layer_index=1,
            header_pin=RaspberryPiHeaderPin.BUTTON_PASS_GPIO19,
        ),
        PanelButton(
            name="F1",
            position_mm=(16.0, -188.0),
            switch_reference="SW8",
            routing_priority=5,
            header_launch_x_offset_mm=0.8,
            fallback_layer_index=0,
            header_pin=RaspberryPiHeaderPin.BUTTON_F1_GPIO20,
        ),
        PanelButton(
            name="F2",
            position_mm=(32.0, -188.0),
            switch_reference="SW9",
            routing_priority=6,
            header_launch_x_offset_mm=-0.8,
            fallback_layer_index=0,
            header_pin=RaspberryPiHeaderPin.BUTTON_F2_GPIO21,
        ),
        PanelButton(
            name="F3",
            position_mm=(48.0, -188.0),
            switch_reference="SW10",
            routing_priority=0,
            header_launch_x_offset_mm=0.8,
            fallback_layer_index=2,
            header_pin=RaspberryPiHeaderPin.BUTTON_F3_GPIO22,
        ),
        PanelButton(
            name="F4",
            position_mm=(64.0, -188.0),
            switch_reference="SW11",
            routing_priority=1,
            header_launch_x_offset_mm=0.8,
            fallback_layer_index=1,
            header_pin=RaspberryPiHeaderPin.BUTTON_F4_GPIO23,
        ),
        PanelButton(
            name="F5",
            position_mm=(80.0, -188.0),
            switch_reference="SW12",
            routing_priority=2,
            header_launch_x_offset_mm=-0.8,
            fallback_layer_index=2,
            header_pin=RaspberryPiHeaderPin.BUTTON_F5_GPIO24,
        ),
    )
)
PANEL_BUTTONS.validate()
