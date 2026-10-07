"""Rear power parts and proposed wiring envelopes in case coordinates.

Rocker dimensions: RA11131100 drawing 38-RA11131100 rev D. Jack body/thread:
722A product drawing and existing case contract. Receptacle envelope remains
conservative; cable dressing, bends and retention require physical review.
"""

from shared.components import BARREL_JACK, power_switch

from .case import CASE_CENTER_OFFSET_Y_MM, CASE_DEPTH_MM, CASE_ROCKER_CUTOUT_MM

REAR_PANEL_Y_MM = CASE_CENTER_OFFSET_Y_MM + CASE_DEPTH_MM / 2
JACK_BODY_MM = BARREL_JACK.require_body_mm()
ROCKER_BODY_MM = power_switch.ROCKER_BODY_MM
ROCKER_FACE_MM = power_switch.ROCKER_FACE_MM
ROCKER_TERMINAL_LENGTH_MM = power_switch.ROCKER_TERMINAL_LENGTH_MM
ROCKER_TERMINAL_PITCH_MM = power_switch.ROCKER_TERMINAL_PITCH_MM
ROCKER_TERMINAL_WIDTH_MM = power_switch.ROCKER_TERMINAL_WIDTH_MM
ROCKER_TERMINAL_THICKNESS_MM = power_switch.ROCKER_TERMINAL_THICKNESS_MM
# Clearance envelope, not detailed supplier geometry, inside the reserved bay.
ROCKER_RECEPTACLE_MM = (6.0, 19.0, 5.0)
assert ROCKER_BODY_MM[0] < CASE_ROCKER_CUTOUT_MM[0]
assert ROCKER_BODY_MM[2] < CASE_ROCKER_CUTOUT_MM[1]
