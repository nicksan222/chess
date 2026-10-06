"""Fixed copper for the LED rail switch Q1 (S6, interface H5), before grid routing.

Q1's source pads (1-3) and drain pads (5-8) each leave outward by a short stub to
their own through-via: the sources into the In2 +5V plane, the drains into the In6
LED_5V plane. Sized for the eFuse's worst case: it is a circuit breaker, so it passes load up to its fast-trip
threshold (about twice the ILM overcurrent threshold) for the ITIMER blanking time (0.46-1.6
ms with C143 = 1 nF) before it trips and retries (TI SLVSFC9C 7.3.5.2).
"""

from __future__ import annotations

import pcbnew

from pcb.definition import native
from pcb.definition.routing.policies import RoutingContext, footprint
from shared import wiring
from shared.electronics.mosfet import DRAIN_PINS, SOURCE_PINS

# Reference of the LED rail switch whose pads get explicit copper.
SWITCH = "Q1"
# Stub width: wide enough for the breaker's worst case (see the module docstring).
STUB_MM = 0.6
VIA_OFFSET_MM = 2.0  # Pad centre to via centre, away from the package.


def route_led_switch(ctx: RoutingContext) -> None:
    """Add one stub and via per Q1 source/drain pad, away from the package centre.

    Runs before the grid router so these power connections are fixed copper the router
    then treats as obstacles, rather than being routed (or starved) like signals.
    """
    board = ctx.board
    module = footprint(board, SWITCH)
    centre = module.GetPosition()
    pads = {pad.GetNumber(): pad for pad in module.Pads()}
    for pins, net in ((SOURCE_PINS, "+5V"), (DRAIN_PINS, wiring.LED_SUPPLY_NET)):
        for pin in pins:
            at = pads[str(pin)].GetPosition()
            outward = 1 if at.x > centre.x else -1
            via = pcbnew.VECTOR2I(at.x + outward * pcbnew.FromMM(VIA_OFFSET_MM), at.y)
            native.add_trace(board, ctx.nets_by_name[net], at, via, width=STUB_MM)
            native.add_via(board, ctx.nets_by_name[net], via)
