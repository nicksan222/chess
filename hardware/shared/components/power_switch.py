"""Approved product: the rear-panel rocker switch (wired to J4, not on the PCB)."""

from .spec import part

# E-Switch RA11131100: snap-in panel rocker, SPST, 0.187 in quick-connect tabs.
POWER_SWITCH = part(
    "POWER_SWITCH",
    "Panel snap-in SPST rocker switch, 0.187 in quick-connect tabs",
    "panel snap-in rocker",
    "E-Switch",
    "RA11131100",
    datasheet="https://configured-product-images.s3.amazonaws.com/2D/specs/RA11131100.pdf",
)
