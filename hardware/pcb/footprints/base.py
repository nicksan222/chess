"""Shared shape of a footprint.

A footprint is the copper a part lands on. Every module in this package describes
one physical package, keyed by the same `package` string the design contract already
records in its bill of materials — so the join between "what the part is" and
"what its pads look like" is a name that already existed, not a new registry.

Pad numbers are datasheet pin numbers, matching the design contract. That is what lets
the connectivity check ask "is pin 21 of U1 connected to pin 1 of RS1" without a
translation table.
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
    pads: tuple["Pad", ...], body: tuple[float, float] = (0.0, 0.0)
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

    @property
    def plated_through(self) -> bool:
        return self.drill > 0.0

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
            drill=self.drill,
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
) -> Footprint:
    """A leaded part lying flat, with its two holes on the X axis.

    Axial parts dominate this board's bill of materials, so their geometry is
    derived from the lead rather than restated part by part.
    """
    from core import rules

    drill = rules.drill_for_lead(lead_diameter)
    pad = rules.pad_for_drill(drill)
    pads = (
        Pad("1", -pitch / 2.0, 0.0, pad, pad, RECT, drill),
        Pad("2", pitch / 2.0, 0.0, pad, pad, ROUND, drill),
    )
    return Footprint(
        package=package,
        description=description,
        pads=pads,
        courtyard=courtyard_for(pads, body),
    )


def dual_inline(
    package: str,
    description: str,
    ways: int,
    row_spacing: float = 7.62,
    pitch: float = 2.54,
    lead_diameter: float = 0.5,
) -> Footprint:
    """A DIP package with its long axis along Y and pin 1 at the top left.

    Pins run down the left column, then back up the right, which is how every
    datasheet numbers them.
    """
    from core import rules

    if ways % 2 != 0:
        raise ValueError(f"{package}: a dual-inline package needs an even pin count")
    per_side = ways // 2
    drill = rules.drill_for_lead(lead_diameter)
    pad = rules.pad_for_drill(drill)
    span = (per_side - 1) * pitch
    pads = []
    for index in range(per_side):
        # Pin 1 is a rectangle so the silkscreen is not the only orientation cue.
        shape = RECT if index == 0 else ROUND
        pads.append(
            Pad(
                str(index + 1),
                -row_spacing / 2.0,
                span / 2.0 - index * pitch,
                pad,
                pad,
                shape,
                drill,
            )
        )
    for index in range(per_side):
        pads.append(
            Pad(
                str(ways - index),
                row_spacing / 2.0,
                span / 2.0 - index * pitch,
                pad,
                pad,
                ROUND,
                drill,
            )
        )
    return Footprint(
        package=package,
        description=description,
        pads=tuple(pads),
        courtyard=courtyard_for(tuple(pads)),
    )


def pin_header(
    package: str,
    description: str,
    columns: int,
    rows: int,
    pitch: float = 2.54,
    lead_diameter: float = 0.64,
) -> Footprint:
    """A pin header numbered the way a Raspberry Pi header is: odd, even, odd.

    Pin 1 sits at the top left, pin 2 beside it, and numbering advances along
    the short axis first.
    """
    from core import rules

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
                    str(number),
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
