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
    """One button: identity, location, header pin and routing hints.

    The last three routing fields only matter to `routing/policies.py` and never
    change connectivity, only how it is routed. `routing_priority` orders all
    button routes and its index also picks the primary route's starting layer;
    `header_launch_x_offset_mm` and `fallback_layer_index` are used only by the
    fallback escape route when the normal grid route cannot reach the Pi header.
    """

    name: str  # Short label; also forms the net name BTN_<name>.
    position_mm: Point  # Switch centre on the board.
    switch_reference: str  # Schematic/PCB reference designator, e.g. "SW1".
    # Lower numbers are routed first (see PanelLayout.routing_order); order matters
    # because earlier routes occupy space the later ones must avoid.
    routing_priority: int
    # Sideways nudge (+/-0.8 mm) of the fallback route's start point relative to
    # the header pad, so neighbouring escapes do not start on the same column.
    header_launch_x_offset_mm: float
    # Preferred internal signal layer (0-2) when the fallback route is used.
    fallback_layer_index: int
    # Typed Pi header pin; carries the GPIO number the firmware must read.
    header_pin: RaspberryPiHeaderPin

    @property
    def legend_position_mm(self) -> Point:
        """Recessed panel legend, independent of the switch net and GPIO."""
        return self.position_mm[0], self.position_mm[1] + (
            8 if self.name == "UP" else -10
        )

    @property
    def gpio(self) -> int:
        """BCM GPIO number, parsed from the typed pin name (e.g. "...GPIO5" -> 5).

        Deriving it from the pin enum keeps a single source for the pin/GPIO pair.
        """
        return int(self.header_pin.name.rsplit("GPIO", maxsplit=1)[1])

    @property
    def net_name(self) -> str:
        """Net between the switch and the Pi header pin, e.g. "BTN_UP"."""
        return f"BTN_{self.name}"

    @property
    def x_mm(self) -> float:
        return self.position_mm[0]

    @property
    def y_mm(self) -> float:
        return self.position_mm[1]


@dataclass(frozen=True, slots=True)
class PanelLayout:
    """The full button set, validated once at import (see `PANEL_BUTTONS`)."""

    buttons: tuple[PanelButton, ...]

    def __iter__(self) -> Iterator[PanelButton]:
        return iter(self.buttons)

    def __len__(self) -> int:
        return len(self.buttons)

    def by_name(self, name: str) -> PanelButton:
        """Look up a button by its label; raises KeyError if unknown."""
        try:
            return next(button for button in self if button.name == name)
        except StopIteration as error:
            raise KeyError(name) from error

    @property
    def routing_order(self) -> tuple[PanelButton, ...]:
        """Buttons sorted by ascending `routing_priority` (route in this order)."""
        return tuple(sorted(self, key=lambda button: button.routing_priority))

    def validate(self) -> None:
        """Reject layouts that would double-assign a pin or leave a gap.

        Duplicate GPIOs/header pins/references would silently short or merge
        buttons, so each identity must be unique; priorities must be a permutation
        so routing order is total; fallback layers must be real signal layers.
        """
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


# D-pad left, OK beside the centered display, functions right, and isolated Reset.
# Electrical identities and routing priorities stay independent of these positions.
PANEL_BUTTONS = PanelLayout(
    (
        PanelButton(
            name="UP",
            position_mm=(-116.0, -178.0),
            switch_reference="SW1",
            routing_priority=11,
            header_launch_x_offset_mm=0.8,
            fallback_layer_index=2,
            header_pin=RaspberryPiHeaderPin.BUTTON_UP_GPIO5,
        ),
        PanelButton(
            name="DOWN",
            position_mm=(-116.0, -202.0),
            switch_reference="SW2",
            routing_priority=10,
            header_launch_x_offset_mm=-0.8,
            fallback_layer_index=1,
            header_pin=RaspberryPiHeaderPin.BUTTON_DOWN_GPIO6,
        ),
        PanelButton(
            name="LEFT",
            position_mm=(-130.0, -190.0),
            switch_reference="SW3",
            routing_priority=9,
            header_launch_x_offset_mm=0.8,
            fallback_layer_index=0,
            header_pin=RaspberryPiHeaderPin.BUTTON_LEFT_GPIO12,
        ),
        PanelButton(
            name="RIGHT",
            position_mm=(-102.0, -190.0),
            switch_reference="SW4",
            routing_priority=8,
            header_launch_x_offset_mm=-0.8,
            fallback_layer_index=2,
            header_pin=RaspberryPiHeaderPin.BUTTON_RIGHT_GPIO13,
        ),
        PanelButton(
            name="OK",
            position_mm=(-84.0, -202.0),
            switch_reference="SW5",
            routing_priority=7,
            header_launch_x_offset_mm=0.8,
            fallback_layer_index=1,
            header_pin=RaspberryPiHeaderPin.BUTTON_OK_GPIO16,
        ),
        PanelButton(
            name="RESET",
            position_mm=(148.0, -204.0),
            switch_reference="SW6",
            routing_priority=3,
            header_launch_x_offset_mm=0.8,
            fallback_layer_index=0,
            header_pin=RaspberryPiHeaderPin.BUTTON_RESET_GPIO17,
        ),
        PanelButton(
            name="PASS",
            position_mm=(120.0, -202.0),
            switch_reference="SW7",
            routing_priority=4,
            header_launch_x_offset_mm=-0.8,
            fallback_layer_index=1,
            header_pin=RaspberryPiHeaderPin.BUTTON_PASS_GPIO19,
        ),
        PanelButton(
            name="F1",
            position_mm=(68.0, -178.0),
            switch_reference="SW8",
            routing_priority=5,
            header_launch_x_offset_mm=0.8,
            fallback_layer_index=0,
            header_pin=RaspberryPiHeaderPin.BUTTON_F1_GPIO20,
        ),
        PanelButton(
            name="F2",
            position_mm=(94.0, -178.0),
            switch_reference="SW9",
            routing_priority=6,
            header_launch_x_offset_mm=-0.8,
            fallback_layer_index=0,
            header_pin=RaspberryPiHeaderPin.BUTTON_F2_GPIO21,
        ),
        PanelButton(
            name="F3",
            position_mm=(120.0, -178.0),
            switch_reference="SW10",
            routing_priority=0,
            header_launch_x_offset_mm=0.8,
            fallback_layer_index=2,
            header_pin=RaspberryPiHeaderPin.BUTTON_F3_GPIO22,
        ),
        PanelButton(
            name="F4",
            position_mm=(68.0, -202.0),
            switch_reference="SW11",
            routing_priority=1,
            header_launch_x_offset_mm=0.8,
            fallback_layer_index=1,
            header_pin=RaspberryPiHeaderPin.BUTTON_F4_GPIO23,
        ),
        PanelButton(
            name="F5",
            position_mm=(94.0, -202.0),
            switch_reference="SW12",
            routing_priority=2,
            header_launch_x_offset_mm=-0.8,
            fallback_layer_index=2,
            header_pin=RaspberryPiHeaderPin.BUTTON_F5_GPIO24,
        ),
    )
)
# Validate at import so a bad edit fails every consumer immediately.
PANEL_BUTTONS.validate()
