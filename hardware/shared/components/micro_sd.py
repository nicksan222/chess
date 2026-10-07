"""Approved product: SanDisk microSD card for the Pi.

Off-board: listed in the human BOM only (`output/exports.EXTRA_ASSEMBLY_PARTS`).
Body size is not recorded; the manufacturer product sheet is linked.
"""

from .spec import part

MICRO_SD = part(
    "MICRO_SD",
    "32 GB high-endurance microSD card",
    "microSD",
    "SanDisk",
    "SDSQQNR-032G-GN6IA",
    datasheet="https://documents.sandisk.com/content/dam/asset-library/en_us/assets/public/sandisk/product/memory-cards/high-endurance-uhs-i-microsd/data-sheet-high-endurance-uhs-i-microsd.pdf",
)

MICRO_SD_CAPACITY_GIGABYTES = 32
