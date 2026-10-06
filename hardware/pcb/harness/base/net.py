"""A board-defined vocabulary for electrical nets, independent of PCB tools."""

from __future__ import annotations

import re
from enum import Enum
from typing import cast


class Net(Enum):
    """Base for the named electrical networks of one board design.

    Define a subclass beside a board declaration, for example
    ``class BoardNet(Net): GROUND = "GND"``. Use its members everywhere a
    component, source or scenario refers to that network. The enum member is
    the authoring identity; its string value is only the output label. Enum
    identity catches misspelled names and keeps equal-looking labels from
    unrelated designs distinct. This lets type checking and runtime validation
    reject a net from another board even when its printed label matches.
    """

    def __init__(self, label: object) -> None:
        """Require a printable label safe to include in generated comments."""
        if not isinstance(label, str) or not re.fullmatch(r"[A-Za-z0-9_+./:-]+", label):
            raise ValueError("net must have a safe net label")

    @property
    def label(self) -> str:
        """Return the board-facing name to show in generated outputs."""
        return cast(str, self.value)
