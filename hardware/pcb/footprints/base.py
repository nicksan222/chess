"""Shared shape of a footprint.

A footprint is the copper a part lands on. Every module in this package describes
one physical package, keyed by the same ``package`` string the design contract
records in its bill of materials. The existing package identity therefore joins
"what the part is" to "what its pads look like" without another registry.

Pad numbers are datasheet pin numbers matching the design contract. This lets the
connectivity check compare component endpoints without a translation table.
"""

from __future__ import annotations

from dataclasses import dataclass
from math import cos, radians, sin

ROUND = "round"
RECT = "rect"
OBLONG = "oblong"
SHAPES = (ROUND, RECT, OBLONG)

# How far a courtyard stands off the copper and body it encloses. A courtyard is
# a keep-out, so it has to be at least as big as the part; deriving it from the
# pads rather than restating it per footprint is what stops the two disagreeing.
COURTYARD_MARGIN_MM = 0.25


def courtyard_for(
    pads: tuple[Pad, ...], body: tuple[float, float] = (0.0, 0.0)
) -> tuple[float, float]:
    """A keep-out that contains every pad, and the part body if it is larger."""
    reach_x = max(abs(pad.x) + pad.width / 2.0 for pad in pads)
    reach_y = max(abs(pad.y) + pad.height / 2.0 for pad in pads)
    return (
        round(max(2.0 * reach_x, body[0]) + 2.0 * COURTYARD_MARGIN_MM, 3),
        round(max(2.0 * reach_y, body[1]) + 2.0 * COURTYARD_MARGIN_MM, 3),
    )


@dataclass(frozen=True)
class Pad:
    """One pad, positioned relative to the footprint origin."""

    number: str
    x: float
    y: float
    width: float
    height: float
    shape: str = ROUND
    drill: float = 0.0
    drill_height: float = 0.0

    @property
    def plated_through(self) -> bool:
        return self.drill > 0.0

    @property
    def drill_size(self) -> tuple[float, float]:
        """Finished drill width/height; unequal axes describe a plated slot."""
        return (self.drill, self.drill_height or self.drill)

    @property
    def net_number(self) -> str:
        """The design contract pin this pad belongs to.

        Some packages have more pads than the design contract has pins: a tactile
        switch's four legs are two shorted pairs, and a DC jack has a spare
        sleeve contact. Those extra pads are named by suffixing a letter, so
        `2b` carries whatever net pin `2` carries.
        """
        return self.number.rstrip("abcdefgh") or self.number

    def rotated(self, degrees: float) -> Pad:
        """The pad as placed, for a footprint rotated about its origin."""
        if degrees % 360 == 0:
            return self
        angle = radians(degrees)
        cosine, sine = cos(angle), sin(angle)
        swap = degrees % 180 == 90
        return Pad(
            number=self.number,
            x=round(self.x * cosine - self.y * sine, 4),
            y=round(self.x * sine + self.y * cosine, 4),
            width=self.height if swap else self.width,
            height=self.width if swap else self.height,
            shape=self.shape,
            drill=(self.drill_height or self.drill) if swap else self.drill,
            drill_height=self.drill
            if swap and self.drill_height
            else self.drill_height,
        )


@dataclass(frozen=True)
class Footprint:
    """The copper and keep-out for one physical package."""

    package: str
    description: str
    pads: tuple[Pad, ...]
    # Width and height of the area the part occupies, used to check that two
    # parts have not been placed on top of each other.
    courtyard: tuple[float, float]

    def pad(self, number: str) -> Pad:
        for pad in self.pads:
            if pad.number == number:
                return pad
        raise KeyError(f"{self.package} has no pad {number}")

    @property
    def numbers(self) -> tuple[str, ...]:
        return tuple(pad.number for pad in self.pads)

    def courtyard_at(self, degrees: float) -> tuple[float, float]:
        width, height = self.courtyard
        return (height, width) if degrees % 180 == 90 else (width, height)


def two_pad_axial(
    package: str,
    description: str,
    pitch: float,
    lead_diameter: float,
    body: tuple[float, float],
    pin_numbers: tuple[str, str],
) -> Footprint:
    """Build a leaded part lying flat, with both holes on the X axis."""
    from core import rules

    drill = rules.drill_for_lead(lead_diameter)
    pad = rules.pad_for_drill(drill)
    pads = (
        Pad(pin_numbers[0], -pitch / 2.0, 0.0, pad, pad, RECT, drill),
        Pad(pin_numbers[1], pitch / 2.0, 0.0, pad, pad, ROUND, drill),
    )
    return Footprint(
        package=package,
        description=description,
        pads=pads,
        courtyard=courtyard_for(pads, body),
    )


def pin_header(
    package: str,
    description: str,
    columns: int,
    rows: int,
    pitch: float = 2.54,
    lead_diameter: float = 0.64,
    pin_numbers: tuple[str, ...] = (),
) -> Footprint:
    """A pin header numbered the way a Raspberry Pi header is: odd, even, odd.

    Pin 1 sits at the top left, pin 2 beside it, and numbering advances along
    the short axis first.
    """
    from core import rules

    count = columns * rows
    if len(pin_numbers) != count:
        raise ValueError(f"{package}: expected {count} semantic pin numbers")
    drill = rules.drill_for_lead(lead_diameter)
    pad = rules.pad_for_drill(drill)
    span_x = (rows - 1) * pitch
    span_y = (columns - 1) * pitch
    pads = []
    for column in range(columns):
        for row in range(rows):
            number = column * rows + row + 1
            shape = RECT if number == 1 else ROUND
            pads.append(
                Pad(
                    pin_numbers[number - 1],
                    -span_x / 2.0 + row * pitch,
                    span_y / 2.0 - column * pitch,
                    pad,
                    pad,
                    shape,
                    drill,
                )
            )
    return Footprint(
        package=package,
        description=description,
        pads=tuple(pads),
        courtyard=courtyard_for(tuple(pads)),
    )
