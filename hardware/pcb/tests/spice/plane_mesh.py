"""Resistive mesh of the +5V, GND and LED_5V planes built from the routed board.

Each plane is a square grid of sheet-resistance resistors: R□ = ρ / t, with ρ the
annealed-copper resistivity (IEC 60028: 1.7241e-8 Ω·m at 20 °C) and t the inner
copper weight in manufacturing.json (1 oz = 0.035 mm). Clearance holes are not drawn
individually: R□ is scaled by outline area / filled area of that plane's actual
zone fill, so the mesh is a smeared approximation, not a field solution. Supply
enters through the measured thermal spokes of the net-derived plane-entry pads; every LED and the Pi header draw their load from
the nodes under their own supply and ground pads. Since S6 the LEDs sit on the
LED_5V plane (In6), joined to the +5V plane only through the LED switch Q1: its
source and drain vias (barrel resistance each) and its on-resistance.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import Path
from typing import cast

import pcbnew

from spice.circuit import SpiceCircuit

PCB_ROOT = Path(__file__).resolve().parents[2]

COPPER_RESISTIVITY_OHM_M = 1.7241e-8
OZ_MM = 0.035
MESH_PITCH_MM = 5.0

SUPPLY_NETS = frozenset({"DC_IN", "DC_FUSED"})
# Contacts that open when the supply is connected (a jack's shunt) carry no supply
# current: (part key, pad). None is on the board since S3a; kept by role.
SWITCHED_CONTACTS = frozenset({("BARREL_JACK", "SLEEVE SHUNT")})
# Pads on a supply part that only carry its bias current (TPS25947 GND, IQ 0.6 mA).
BIAS_ONLY = frozenset({("EFUSE", "8")})
# Plated via barrel: board thickness through IPC-6012 Class 2 wall (ampacity test).
VIA_WALL_MM = 0.018  # PCBWay standard floor (S4c, as tests/board/test_ampacity.py)
BOARD_THICKNESS_MM = 1.6
PLANE_LAYERS = {"+5V": pcbnew.In2_Cu, "GND": pcbnew.In1_Cu, "LED_5V": pcbnew.In6_Cu}
LED_SWITCH = "Q1"
SWITCH_SOURCE_PADS = ("1", "2", "3")
SWITCH_DRAIN_PADS = ("5", "6", "7", "8")


@dataclass(frozen=True)
class Load:
    """A current sink between two plane points: a part's supply pad and ground pad, and its current."""

    name: str
    supply: pcbnew.VECTOR2I
    ground: pcbnew.VECTOR2I
    amps: float
