"""Purchasing identity and manufacturer dimensions, with no PCB tool dependency."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Product:
    """The exact manufactured item selected for a component kind.

    ``key`` is a stable design name used by the authoring model;
    ``manufacturer`` and ``part_number``
    identify what to purchase. ``package`` names the physical casing and lead
    style. ``body_mm`` is the nominal length, width and height from its drawing.
    The body is distinct from the larger courtyard reserved for assembly.
    ``datasheet`` is the evidence for these facts, not a simulation model.
    """

    key: str
    manufacturer: str
    part_number: str
    package: str
    body_mm: tuple[float, float, float]
    datasheet: str

    def __post_init__(self) -> None:
        """Fail early when a product cannot be identified or measured."""
        if not all(
            value.strip()
            for value in (
                self.key,
                self.manufacturer,
                self.part_number,
                self.package,
                self.datasheet,
            )
        ):
            raise ValueError("product identity, package and datasheet are required")
        if len(self.body_mm) != 3 or any(
            not math.isfinite(value) or value <= 0 for value in self.body_mm
        ):
            raise ValueError("product body must have three positive dimensions")
