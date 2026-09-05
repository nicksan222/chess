"""Typed access to shared definitions and the reviewed board contract."""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path
from typing import Protocol

from domain.validation import is_string_mapping
from shared import dimensions as shared_dimensions
from shared import wiring as shared_wiring

PCB_ROOT = Path(__file__).resolve().parents[1]
HARDWARE_ROOT = PCB_ROOT.parent
REPOSITORY_ROOT = HARDWARE_ROOT.parent
NETLIST_PATH = PCB_ROOT / "board" / "data" / "netlist.json"
PROJECT_NAME = "board"


class DimensionsSource(Protocol):
    """Read-only mechanical values consumed by PCB placement and markings."""

    @property
    def GRID_COUNT(self) -> int: ...

    @property
    def SQUARE_SIZE_MM(self) -> float: ...

    @property
    def PLAYING_SPAN_MM(self) -> float: ...

    @property
    def LED_POSITION_MM(self) -> tuple[float, float]: ...

    @property
    def BOARD_SQUARE_CENTERS_MM(
        self,
    ) -> tuple[tuple[int, int, float, float], ...]: ...

    @property
    def PCB_SUPPORT_POSITIONS_MM(self) -> tuple[tuple[float, float], ...]: ...

    @property
    def PANEL_BUTTON_POSITIONS_MM(self) -> tuple[tuple[float, float], ...]: ...

    @property
    def PANEL_ORIGIN_Y_MM(self) -> float: ...

    @property
    def PI_BAY_CENTER_MM(self) -> tuple[float, float]: ...

    @property
    def PI_HEADER_ROTATION_DEG(self) -> float: ...

    @property
    def EXPANDER_POSITIONS_BY_BANK_MM(
        self,
    ) -> Mapping[str, tuple[float, ...]]: ...

    @property
    def PCB_STRIP_PLACEMENTS_MM(
        self,
    ) -> Mapping[str, tuple[float, ...]]: ...


class WiringNamesSource(Protocol):
    @property
    def BUTTON_NAMES(self) -> tuple[str, ...]: ...

    @property
    def FILES(self) -> str: ...


def dimensions() -> DimensionsSource:
    return shared_dimensions


def names() -> WiringNamesSource:
    return shared_wiring


def _string_mapping(value: object, *, label: str) -> Mapping[str, object]:
    if not is_string_mapping(value):
        raise ValueError(f"{label} must be an object with string keys")
    return value


def netlist() -> Mapping[str, object]:
    """Load the JSON contract while containing its untyped data at this boundary."""
    if not NETLIST_PATH.is_file():
        raise RuntimeError(
            f"{NETLIST_PATH} is missing. The PCB connectivity contract is required."
        )
    published: object = json.loads(NETLIST_PATH.read_text())
    root = _string_mapping(published, label="netlist")
    if root.get("schema") != 1:
        raise RuntimeError(f"Unsupported netlist schema {root.get('schema')}")
    projects = _string_mapping(root.get("projects"), label="netlist projects")
    try:
        project = projects[PROJECT_NAME]
    except KeyError as error:
        raise RuntimeError(f"Netlist has no {PROJECT_NAME!r} project") from error
    return _string_mapping(project, label=f"{PROJECT_NAME} project")
