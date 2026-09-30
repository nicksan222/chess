"""Approved power supply product."""

from .spec import part

POWER_SUPPLY = part(
    "POWER_SUPPLY",
    "5 V 2 A regulated desktop supply with 5.5x2.1 mm plug",
    "external PSU",
    "MEAN WELL",
    "GST12A05-P1J",
    datasheet="https://www.meanwell.com/Upload/PDF/GST12A/GST12A-SPEC.PDF",
)
