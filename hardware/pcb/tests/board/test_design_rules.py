"""The U74 fine-pitch exception stays scoped to U74 (lead-approved, S4b).

`output/exports.render_design_rules()` writes the KiCad custom rules beside the
board: board-wide 0.30 mm clearance and 0.31 mm tracks, then 0.15 / 0.20 mm only for
U74's pads and copper crossing its courtyard. These tests check the rule text names
U74 alone (a mutation naming another part fails), and that the routed board needs
the exception nowhere else: KiCad's DRC without the U74 rules may only flag items at
U74.
"""

import json
import math
import os
import re
import shutil
import subprocess
import tempfile
import unittest
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import TypedDict, cast

import pcbnew

from pcb.definition import rules
from pcb.definition.output import exports

PCB_ROOT = Path(__file__).resolve().parents[2]


class NetClass(TypedDict):
    """One KiCad netclass entry (clearance and track width) as read from the project JSON."""

    clearance: float
    track_width: float


class NetClasses(TypedDict):
    """The `classes` list inside the project's net settings."""

    classes: list[NetClass]


class NetSettings(TypedDict):
    """The `net_settings` section of the project file."""

    net_settings: NetClasses


class Position(TypedDict):
    """An (x, y) position in a DRC report."""

    x: float
    y: float


class DrcItem(TypedDict):
    """One item (description, position, id) a DRC violation refers to."""

    description: str
    pos: Position
    uuid: str
