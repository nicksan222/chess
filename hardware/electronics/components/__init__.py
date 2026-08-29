"""Catalog of single components. One physical part per module.

Adding a part is adding a module here that binds a `Component` to an
UPPER_CASE name. This package discovers it, so no import list, no registry and
no bill-of-materials code has to be edited to keep up.
"""

from __future__ import annotations

import importlib
import pkgutil
from types import FunctionType

from .base import Component

CATALOG: dict[str, Component] = {}


def _export(module) -> list[str]:
    """Publish this module's parts and its own factory helpers."""
    names = []
    for name, value in vars(module).items():
        if name.startswith("_"):
            continue
        if isinstance(value, Component) and name.isupper():
            CATALOG[name] = value
        elif not (
            isinstance(value, FunctionType) and value.__module__ == module.__name__
        ):
            continue
        globals()[name] = value
        names.append(name)
    return names


def _discover() -> list[str]:
    found: list[str] = []
    for info in sorted(pkgutil.iter_modules(__path__), key=lambda m: m.name):
        if info.name == "base":
            continue
        found += _export(importlib.import_module(f"{__name__}.{info.name}"))
    return found


__all__ = ["CATALOG", "Component", *sorted(_discover())]
