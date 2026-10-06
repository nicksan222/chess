"""Approved land patterns against hand-typed datasheet facts.

Every row below is copied by hand from the cited manufacturer document, not derived
from `shared.electronics` enums or `definition.parts` constructors. Pad centres,
copper sizes and drills use the datasheet's own top view: millimetres, package centre
origin, Y up. When a template is drawn in a frame rotated from the drawing (to keep
an existing board placement), `frame_rotation_deg` states that pure rotation; it
preserves chirality, so a mirrored or renumbered land still fails. `function` is the
repository's semantic name for the datasheet pin and `rail` the supply net that pin
must reach on the native board. Parts whose land could not be sourced are listed in
`UNVERIFIED` with the reason, never given invented dimensions.
"""

import math
import unittest
from dataclasses import dataclass
from itertools import pairwise
from typing import ClassVar

import pcbnew

from pcb.definition import board, native
from pcb.definition.parts.catalog import PCB_PARTS
from pcb.definition.parts.part import DrawingView
from pcb.definition.verification import UNVERIFIED

TOLERANCE_MM = 0.01

Range = tuple[float, float]
Point = tuple[float, float]


@dataclass(frozen=True)
class LandPad:
    """One datasheet pad: number, datasheet pin name and function, supply rail (if any), and its centre, copper size and drill in the datasheet top view (mm)."""

    number: str
    datasheet_name: str
    function: str | None
    rail: str | None = None
    centre_mm: Point | None = None
    size_mm: Point | None = None
    drill_mm: Point | None = None


@dataclass(frozen=True)
class LandPattern:
    """One part's golden facts: product, package, cited source, body size ranges, pads, and the frame rotation and polarity pad where relevant."""

    part_key: str
    mpn: str
    package: str
    source: str
    body_ranges_mm: tuple[Range, Range, Range] | None
    pads: tuple[LandPad, ...]
    frame_rotation_deg: int = 0
    polarity_pad: str | None = None
    internal_groups: tuple[tuple[str, ...], ...] = ()
    # The datasheet draws the land from the side the part sits on (catalogue
    # convention, e.g. JST VH p4 note 1), unless it is fixed by a mating part
    # seen from the board top (the Pi header).
    drawn_from_board_top: bool = False
