"""Approved product: Mean Well GST12A05-P1J 5 V 2 A supply (off-board, human BOM only).

This external supply feeds the board's DC input.
"""

from .spec import part

POWER_SUPPLY = part(
    "POWER_SUPPLY",
    "5 V 2 A regulated desktop supply with 5.5x2.1 mm plug",
    "external PSU",
    "MEAN WELL",
    "GST12A05-P1J",
    datasheet="https://www.meanwell.com/Upload/PDF/GST12A/GST12A-SPEC.PDF",
)
