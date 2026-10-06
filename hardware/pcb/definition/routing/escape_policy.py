"""Per-product signal and power escape choices for PCB routing.

Role: for each SMD product, how far (and in which direction) a pad's escape via sits from
its pad. These distances are not arbitrary: they keep the via ring away from neighbouring
pads and the solder-mask web above the fab minimum (`tests/board/test_silkscreen.py`,
`test_decoupling.py`), and keep the grid router's lanes open. Used by
`routing/policies.py`. Changing one means re-running the board review.
"""

import pcbnew

from pcb.definition import rules
from pcb.definition.parts.catalog import PCB_PARTS
from shared.components import (
    AHCT125,
    HALL_SENSOR,
    LED_ENABLE_GATE,
    OLED_HEADER,
    SK9822,
    TCA9554,
    TVS_12V0,
)

# Products with surface-mount pads; only these need an escape policy.
SMD_MPNS = {
    part.spec.mpn
    for part in PCB_PARTS.values()
    if any(p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD for p in part.template.Pads())
}


def signal_escape_distance_mm(mpn: str, pin_number: str) -> float:
    """Distance (mm) a signal pad's escape via sits from its pad; raises for unknown parts.

    The staggers (by pin number) keep neighbouring escape vias from touching on fine pitch.
    """
    if mpn not in SMD_MPNS:
        raise KeyError(f"no signal escape for {mpn}")
    if mpn in (AHCT125.mpn, TCA9554.mpn):
        return 2.0 + (int(pin_number) - 1) % 4
    if mpn == OLED_HEADER.mpn:
        # 1.0 mm pitch: stagger neighbouring escape vias by 1.5 mm.
        return 2.0 if int(pin_number) % 2 else 3.5
    return 3.0 if mpn == HALL_SENSOR.mpn else 2.0


# Smallest pad-centre-to-via offset beyond the pad half-extent that keeps the fab's
# solder-mask dam between the tented via ring and the pad's mask opening.
VIA_MASK_WEB_REACH_MM = (
    rules.VIA_PAD_MM / 2 + rules.MASK_EXPANSION_MM + rules.PCBWAY_MIN_MASK_DAM_MM + 0.05
)


def power_escape_policy(mpn: str, pin_number: str) -> tuple[float, bool]:
    """(distance in mm, whether the escape is radial) for a rail (supply/ground) pad."""
    if mpn not in SMD_MPNS:
        raise KeyError(f"no power escape for {mpn}")
    if mpn == TCA9554.mpn:
        # Corner rails (8 GND, 16 VCC) have no neighbour beyond them: short escape.
        if pin_number in ("8", "16"):
            return 0.0, True
        return signal_escape_distance_mm(mpn, pin_number), True
    if mpn == OLED_HEADER.mpn:
        return (0.4 if int(pin_number) % 2 else 2.9), False
    if mpn == SK9822.mpn:
        # 1.25 mm leaves a 0.25 mm mask web (1.25 - 0.5 pad - 0.45 via - 0.05 mask)
        # and keeps the grid router's lanes open.
        return 1.25, False
    if mpn == LED_ENABLE_GATE.mpn:
        # SOT-23-6 GND (2) sits 0.95 mm from the tied-high input: stagger its via
        # one via pitch further out so the two vias clear each other.
        return (2.4 if pin_number == "2" else 0.4), True
    return (1.2, True) if mpn == AHCT125.mpn else (0.4, False)


def uses_vertical_power_escape(mpn: str) -> bool:
    """Corner LED rail pads escape along Y, beside the pad, clear of chain lanes."""
    return mpn == SK9822.mpn


def uses_horizontal_signal_escape(mpn: str) -> bool:
    """SOIC parts whose signal escapes run sideways out of the pad rows."""
    return mpn in (AHCT125.mpn, TCA9554.mpn)


# The TVS carries the supply current in a reverse-plug fault until the fuse opens:
# a 1.0 mm stub (IPC-2221, 1 oz outer, 10 °C: 2.3 A) into three plated vias.
FAULT_STUB_WIDTH_MM = 1.0
FAULT_VIA_COUNT = 3
FAULT_VIA_PITCH_MM = 1.2


def carries_fault_current(mpn: str) -> bool:
    """True for the TVS, whose pads get the wide stub and via fan-out above."""
    return mpn == TVS_12V0.mpn
