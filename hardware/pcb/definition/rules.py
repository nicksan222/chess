"""PCB manufacturing limits and chosen design rules.

Role: the numeric design rules for the board, in millimetres. `PCBWAY_MIN_*` are the
fabricator's process limits; the other constants are the (more conservative) values
this design actually uses. `validate()` refuses a design whose chosen values fall
below the process limits. `native.py` applies these to KiCad's design settings and
`exports.py` records them in review output, so editing a value here changes the
routing, DRC settings and reports together. Passing validation is not a fabrication
quote or a guarantee the board is manufacturable.
"""

from __future__ import annotations

from enum import StrEnum

# --- Fabricator process minimums (the floor the design must stay above) -------
# PCBWay capabilities page (per the 2026-10-06 manufacturing review): 5/6 mil
# trace/space for 1 oz (35 um) finished outer copper; 4/4 mil is for 18 um only.
PCBWAY_MIN_TRACE_WIDTH_MM = 0.127

PCBWAY_MIN_CLEARANCE_MM = 0.152

PCBWAY_MIN_DRILL_MM = 0.2

PCBWAY_MIN_ANNULAR_RING_MM = 0.13

PCBWAY_MIN_SILK_LINE_MM = 0.15

PCBWAY_MIN_SILK_TEXT_HEIGHT_MM = 0.8

PCBWAY_MIN_MASK_DAM_MM = 0.1

# --- Chosen design values -----------------------------------------------------
# Default signal trace width, comfortably above the process minimum.
TRACE_WIDTH_MM = 0.31

# Wider copper for power traces than for signals (validate() keeps it >= signal).
POWER_TRACE_WIDTH_MM = 1.5

# Minimum copper-to-copper spacing between different nets.
CLEARANCE_MM = 0.30

# Lead-approved S4b exception, U74 only (generated chess-board.kicad_dru): the TI
# RPW0010A land has 0.2 mm pad gaps and 0.45 mm-pitch pins. Items that are U74 pads,
# or U74 escape copper inside its courtyard, may sit 0.16 mm apart (S4c: above
# the 6 mil 1 oz minimum); tracks there may be 0.20 mm wide. Both stay above the
# PCBWay minimums above.
FINE_PITCH_CLEARANCE_MM = 0.16
FINE_PITCH_TRACE_WIDTH_MM = 0.20
# Escape copper keeps the exception up to this far outside U74's courtyard, where
# the 0.45 mm-pitch escapes have fanned out to the board clearance (S4c r-m2); the
# router cuts any longer track there (`routing/efuse.split_fine_pitch_escapes`).
FINE_PITCH_ESCAPE_MARGIN_MM = 0.6
FINE_PITCH_REFERENCE = "U74"

# Via geometry: drill and finished pad; their difference sets the annular ring.
VIA_DRILL_MM = 0.4

VIA_PAD_MM = 0.9

# Copper-to-hole-edge spacing, and edge-to-edge spacing between two drilled holes.
HOLE_CLEARANCE_MM = 0.25

HOLE_TO_HOLE_MM = 0.25

# Extra drill diameter over a through-hole lead so the lead fits (see drill_for_lead).
THT_DRILL_CLEARANCE_MM = 0.3

# Copper ring left around a through-hole drill on each side (see pad_for_drill).
THT_ANNULAR_RING_MM = 0.4

# How much the soldermask opening exceeds the pad on each side.
MASK_EXPANSION_MM = 0.05

# Silkscreen stroke width and label text height, above the process minimums.
SILK_LINE_MM = 0.2

SILK_TEXT_HEIGHT_MM = 1.0

# Drawn widths for the board outline, courtyards and fabrication-layer lines.
OUTLINE_LINE_MM = 0.05

COURTYARD_LINE_MM = 0.05

FAB_LINE_MM = 0.1

# Clearance a copper pour (zone) keeps from other nets.
POUR_CLEARANCE_MM = 0.5

# Board-wide copper-to-edge clearance (KiCad's copper edge clearance); the router
# also uses it for tracks and vias. The rail planes are inset a further 1.0 mm
# in `native.add_power_planes`.
POUR_TO_OUTLINE_MM = 0.5

# `validate()` pins this at 8: In1-In3 are the rail planes (GND, +5V, +3V3),
# In4-In6 internal signal layers, plus F.Cu/B.Cu for routed copper.
COPPER_LAYERS = 8


def drill_for_lead(lead_diameter_mm: float) -> float:
    """Hole size for a through-hole lead of a given diameter."""
    return round(lead_diameter_mm + THT_DRILL_CLEARANCE_MM, 3)


def pad_for_drill(drill_mm: float) -> float:
    """Pad diameter giving the design's annular ring around a hole."""
    return round(drill_mm + 2.0 * THT_ANNULAR_RING_MM, 3)


def annular_ring(pad_mm: float, drill_mm: float) -> float:
    """Copper ring width on each side of a hole: (pad - drill) / 2."""
    return round((pad_mm - drill_mm) / 2.0, 4)


def validate() -> None:
    """Refuse any chosen geometry the manufacturer cannot make."""
    if TRACE_WIDTH_MM < PCBWAY_MIN_TRACE_WIDTH_MM:
        raise ValueError("Signal trace is narrower than the process allows")
    if POWER_TRACE_WIDTH_MM < TRACE_WIDTH_MM:
        raise ValueError("Power trace should not be narrower than a signal trace")
    if CLEARANCE_MM < PCBWAY_MIN_CLEARANCE_MM:
        raise ValueError("Clearance is tighter than the process allows")
    if not (PCBWAY_MIN_CLEARANCE_MM <= FINE_PITCH_CLEARANCE_MM < CLEARANCE_MM):
        raise ValueError("The U74 clearance exception must sit between fab and board")
    if not (PCBWAY_MIN_TRACE_WIDTH_MM <= FINE_PITCH_TRACE_WIDTH_MM < TRACE_WIDTH_MM):
        raise ValueError("The U74 track exception must sit between fab and board")
    if POUR_CLEARANCE_MM < CLEARANCE_MM:
        raise ValueError("A pour must pull back at least as far as a signal")
    if VIA_DRILL_MM < PCBWAY_MIN_DRILL_MM:
        raise ValueError("Via drill is smaller than the process allows")
    if annular_ring(VIA_PAD_MM, VIA_DRILL_MM) < PCBWAY_MIN_ANNULAR_RING_MM:
        raise ValueError("Via annular ring is thinner than the process allows")
    if THT_ANNULAR_RING_MM < PCBWAY_MIN_ANNULAR_RING_MM:
        raise ValueError("Through-hole annular ring is thinner than the process allows")
    if SILK_LINE_MM < PCBWAY_MIN_SILK_LINE_MM:
        raise ValueError("Silkscreen line is thinner than the process allows")
    if SILK_TEXT_HEIGHT_MM < PCBWAY_MIN_SILK_TEXT_HEIGHT_MM:
        raise ValueError("Silkscreen text is smaller than the process can hold")
    if OUTLINE_LINE_MM <= 0.0:
        raise ValueError("The board outline needs a drawn width")
    if COPPER_LAYERS != 8:
        raise ValueError(
            "Three rail planes and three signal layers require eight layers"
        )
    if MASK_EXPANSION_MM <= 0.0:
        raise ValueError("Soldermask must open wider than the pad it clears")


class Net(StrEnum):
    """Names of the power nets shared across assemblies and routing policy.

    Values are the literal KiCad net names, so they can be compared directly with
    names read back from the board.
    """

    GROUND = "GND"
    FIVE_VOLTS = "+5V"
    LED_FIVE_VOLTS = "LED_5V"
    THREE_VOLTS_THREE = "+3V3"
    DC_INPUT = "DC_IN"
    DC_FUSED = "DC_FUSED"
