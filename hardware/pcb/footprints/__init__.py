"""Catalog of footprints, one physical package per module.

Adding a footprint is adding a module here that binds a `Footprint` to an
UPPER_CASE name. This package discovers it and indexes it by its `package`
string, which is the same string the schematic records, so nothing else needs
editing to keep up.

The same discipline as `hardware/electronics/components`, for the same reason.
"""

from __future__ import annotations

import importlib
import pkgutil
from types import FunctionType

from .base import Footprint, Pad

CATALOG: dict[str, Footprint] = {}


def _export(module) -> list[str]:
    names = []
    for name, value in vars(module).items():
        if name.startswith("_"):
            continue
        if isinstance(value, Footprint) and name.isupper():
            if value.package in CATALOG:
                raise RuntimeError(
                    f"Two footprints claim package {value.package!r}: "
                    f"{CATALOG[value.package].description} and {value.description}"
                )
            CATALOG[value.package] = value
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


def for_package(package: str) -> Footprint:
    """The footprint a schematic package string resolves to."""
    if package not in CATALOG:
        raise KeyError(
            f"No footprint for package {package!r}. Add a module to "
            f"hardware/pcb/footprints. Known: {sorted(CATALOG)}"
        )
    return CATALOG[package]


__all__ = ["CATALOG", "Footprint", "Pad", "for_package", *sorted(_discover())]
