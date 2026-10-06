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
from shared.components import AHCT125, HALL_SENSOR, TCA9554

SMD_MPNS = {
    part.spec.mpn
    for part in PCB_PARTS.values()
    if any(p.GetAttribute() == pcbnew.PAD_ATTRIB_SMD for p in part.template.Pads())
}


def signal_escape_distance_mm(mpn: str, pin_number: str) -> float:
    if mpn not in SMD_MPNS:
        raise KeyError(f"no signal escape for {mpn}")
    if mpn in (AHCT125.mpn, TCA9554.mpn):
        return 2.0 + (int(pin_number) - 1) % 4
    return 3.0 if mpn == HALL_SENSOR.mpn else 2.0


def power_escape_policy(mpn: str, pin_number: str) -> tuple[float, bool]:
    if mpn not in SMD_MPNS:
        raise KeyError(f"no power escape for {mpn}")
    if mpn == TCA9554.mpn:
        return signal_escape_distance_mm(mpn, pin_number), True
    return (1.2, True) if mpn == AHCT125.mpn else (0.4, False)


def uses_horizontal_signal_escape(mpn: str) -> bool:
    return mpn in (AHCT125.mpn, TCA9554.mpn)
