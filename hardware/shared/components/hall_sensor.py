"""Approved hall sensor product."""

from .spec import part

HALL_SENSOR = part(
    "HALL_SENSOR",
    "20 Hz omnipolar active-low Hall-effect sensor",
    "SOT-23-3",
    "Texas Instruments",
    "DRV5032FCDBZR",
    (2.92, 1.30, 1.12),
    "https://www.ti.com/lit/ds/symlink/drv5032.pdf",
)
