"""Approved product: SN74AHCT125DR quad buffer (LED data/clock level shifter, U5)."""

from .spec import part

AHCT125 = part(
    "AHCT125",
    "Quad 3.3 V to 5 V logic buffer",
    "SOIC-14 1.27 mm",
    "Texas Instruments",
    "SN74AHCT125DR",
    (8.7, 6.2, 1.75),
    "https://www.ti.com/lit/ds/symlink/sn74ahct125.pdf",
)
