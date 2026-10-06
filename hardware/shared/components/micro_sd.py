"""Approved product: SanDisk microSD card for the Pi.

Off-board: listed in the human BOM only (`output/exports.EXTRA_ASSEMBLY_PARTS`).
No body size or datasheet is recorded.
"""

from .spec import part

MICRO_SD = part(
    "MICRO_SD",
    "32 GB high-endurance microSD card",
    "microSD",
    "SanDisk",
    "SDSQQNR-032G-GN6IA",
)
