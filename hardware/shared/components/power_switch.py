"""Approved product: the rear-panel rocker switch (wired to J4, not on the PCB)."""

from .spec import part

# E-Switch RA11131100: snap-in panel rocker, SPST, 0.187 in quick-connect tabs.
POWER_SWITCH = part(
    "POWER_SWITCH",
    "Panel snap-in SPST rocker switch, 0.187 in quick-connect tabs",
    "panel snap-in rocker",
    "E-Switch",
    "RA11131100",
    (18.9, 11.6, 12.9),
    datasheet="https://configured-product-images.s3.amazonaws.com/2D/specs/RA11131100.pdf",
)

# Intrinsic RA11131100 geometry from drawing 38-RA11131100 rev D.
ROCKER_BODY_MM = POWER_SWITCH.require_body_mm()
ROCKER_FACE_MM = (21.0, 6.0, 15.0)
ROCKER_CUTOUT_MM = (19.4, 13.0)
ROCKER_PANEL_RANGE_MM = (1.25, 2.0)
ROCKER_TERMINAL_LENGTH_MM = 7.0
ROCKER_TERMINAL_PITCH_MM = 7.0
ROCKER_TERMINAL_WIDTH_MM = 4.8
ROCKER_TERMINAL_THICKNESS_MM = 0.8
