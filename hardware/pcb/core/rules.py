"""Fabrication limits and the geometry this board actually uses.

There is no design-rule checker in this toolchain, so the rules live here as
numbers and the tests assert the board stays inside them. That is a weaker
guarantee than a real DRC over finished copper, and it is stated plainly rather
than implied: these checks catch a geometry mistake, not a routing mistake.

Two sets of numbers. `PCBWAY_*` are the manufacturer's stated capabilities for a
standard two-layer board, and are not ours to choose. `TRACE_*`, `PAD_*` and the
rest are what this design uses, chosen with a wide margin so a prototype is never
near a process limit. `validate()` refuses any choice that is not inside the
capability, so raising a limit cannot silently produce an unmanufacturable board.

Capabilities are from PCBWay's published two-layer capability table. Confirm them
against the current page before an order; a fab can change its process.
"""

from __future__ import annotations

# --- Manufacturer capability, standard two-layer process --------------------
PCBWAY_MIN_TRACE_WIDTH_MM = 0.1
PCBWAY_MIN_CLEARANCE_MM = 0.1
PCBWAY_MIN_DRILL_MM = 0.2
PCBWAY_MIN_ANNULAR_RING_MM = 0.13
PCBWAY_MIN_SILK_LINE_MM = 0.15
PCBWAY_MIN_SILK_TEXT_HEIGHT_MM = 0.8
PCBWAY_MIN_MASK_DAM_MM = 0.1
PCBWAY_MAX_BOARD_MM = (500.0, 1000.0)

# --- What this board uses ---------------------------------------------------
# Four times the process minimum. This board is hand-soldered and hand-reviewed;
# there is no reason to be anywhere near the limit.
TRACE_WIDTH_MM = 0.4
POWER_TRACE_WIDTH_MM = 1.0
CLEARANCE_MM = 0.4

VIA_DRILL_MM = 0.4
VIA_PAD_MM = 0.9

# Through-hole pads: the drill clears the lead, and the ring is generous because
# a hand-soldered joint gets reworked more than a machine-placed one.
THT_DRILL_CLEARANCE_MM = 0.3
THT_ANNULAR_RING_MM = 0.4

MASK_EXPANSION_MM = 0.05
SILK_LINE_MM = 0.2
SILK_TEXT_HEIGHT_MM = 2.0
OUTLINE_LINE_MM = 0.15

# Copper pours pull back further than the signal clearance, because a pour edge
# is the one place a small etching error meets a large amount of copper.
POUR_CLEARANCE_MM = 0.5
POUR_TO_OUTLINE_MM = 0.5

BOARD_THICKNESS_MM = 1.6
COPPER_LAYERS = 2


def drill_for_lead(lead_diameter_mm: float) -> float:
    """Hole size for a through-hole lead of a given diameter."""
    return round(lead_diameter_mm + THT_DRILL_CLEARANCE_MM, 3)


def pad_for_drill(drill_mm: float) -> float:
    """Pad diameter giving the design's annular ring around a hole."""
    return round(drill_mm + 2.0 * THT_ANNULAR_RING_MM, 3)


def annular_ring(pad_mm: float, drill_mm: float) -> float:
    return round((pad_mm - drill_mm) / 2.0, 4)


def validate() -> None:
    """Refuse any chosen geometry the manufacturer cannot make."""
    if TRACE_WIDTH_MM < PCBWAY_MIN_TRACE_WIDTH_MM:
        raise ValueError("Signal trace is narrower than the process allows")
    if POWER_TRACE_WIDTH_MM < TRACE_WIDTH_MM:
        raise ValueError("Power trace should not be narrower than a signal trace")
    if CLEARANCE_MM < PCBWAY_MIN_CLEARANCE_MM:
        raise ValueError("Clearance is tighter than the process allows")
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
    if COPPER_LAYERS != 2:
        raise ValueError("This design is two-layer; review every rule before changing")
    if MASK_EXPANSION_MM <= 0.0:
        raise ValueError("Soldermask must open wider than the pad it clears")


validate()


if __name__ == "__main__":
    print(
        "PCB rules valid: "
        f"{TRACE_WIDTH_MM:g} mm signal / {POWER_TRACE_WIDTH_MM:g} mm power traces, "
        f"{CLEARANCE_MM:g} mm clearance, "
        f"{VIA_DRILL_MM:g} mm vias in {VIA_PAD_MM:g} mm pads "
        f"({annular_ring(VIA_PAD_MM, VIA_DRILL_MM):g} mm ring); "
        f"process floor is {PCBWAY_MIN_TRACE_WIDTH_MM:g}/"
        f"{PCBWAY_MIN_CLEARANCE_MM:g} mm"
    )
