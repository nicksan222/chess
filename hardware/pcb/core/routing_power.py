"""Native KiCad routing and plane fanout for board power."""

from __future__ import annotations

import pcbnew

from components.barrel_jack import BarrelJackPin, DC_INPUT_JACK
from components.fuse import FusePin, INPUT_FUSE
from components.power_switch import MAIN_POWER_SWITCH, PowerSwitchPin
from core import kicad, routing_common as common, rules
from core.nets import Net


def route_input_power(board, net_by_name, pads) -> None:
    """Route protected input current around the jack contacts and signal lanes."""
    routes = (
        (
            Net.DC_INPUT,
            DC_INPUT_JACK.endpoint(BarrelJackPin.CENTRE_POSITIVE),
            INPUT_FUSE.endpoint(FusePin.UNFUSED_INPUT),
            # Run below the rotated PJ-102A body; its offset grounded slot sits
            # above the centre-positive terminal at y=393.3 mm.
            403.0,
        ),
        (
            Net.DC_FUSED,
            INPUT_FUSE.endpoint(FusePin.FUSED_OUTPUT),
            MAIN_POWER_SWITCH.endpoint(PowerSwitchPin.FUSED_INPUT),
            414.0,
        ),
    )
    for name, left, right, lane_y in routes:
        net = net_by_name[name]
        start, end = pads[left].GetPosition(), pads[right].GetPosition()
        first = pcbnew.VECTOR2I(start.x, pcbnew.FromMM(lane_y))
        second = pcbnew.VECTOR2I(end.x, pcbnew.FromMM(lane_y))
        kicad.add_trace(board, net, start, first, width=rules.POWER_TRACE_WIDTH_MM)
        kicad.add_trace(board, net, first, second, width=rules.POWER_TRACE_WIDTH_MM)
        kicad.add_trace(board, net, second, end, width=rules.POWER_TRACE_WIDTH_MM)


def _power_escape_position(module, pad):
    """Choose a short fanout that clears its package and nearby signal lanes."""
    at = pad.GetPosition()
    centre = module.GetPosition()
    dx, dy = at.x - centre.x, at.y - centre.y
    reference = module.GetReference()

    if reference in common.EXPANDER_REFERENCES:
        # Stagger adjacent SOIC vias instead of building a solid via wall.
        escape_mm = 2.0 + (int(pad.GetNumber()) - 1) % 4
        distance = pcbnew.FromMM(escape_mm)
        escaped = pcbnew.VECTOR2I(
            at.x + (distance if dx >= 0 else -distance), at.y
        )
    elif reference == "U5":
        distance = pcbnew.FromMM(1.2)
        escaped = pcbnew.VECTOR2I(
            at.x + (distance if dx >= 0 else -distance), at.y
        )
    else:
        length = max(1, round((dx * dx + dy * dy) ** 0.5))
        distance = pcbnew.FromMM(0.4)
        escaped = pcbnew.VECTOR2I(
            at.x + dx * distance // length,
            at.y + dy * distance // length,
        )

    # The Pi/header bay is unusually dense. Push these vias beyond its parallel
    # launch lanes rather than leaving them in the normal 0.4 mm fanout ring.
    if (
        pcbnew.FromMM(170) < at.x < pcbnew.FromMM(230)
        and pcbnew.FromMM(340) < at.y < pcbnew.FromMM(350)
    ):
        escaped = pcbnew.VECTOR2I(
            at.x + (pcbnew.FromMM(6.0) if dx > 0 else -pcbnew.FromMM(6.0)),
            at.y,
        )
    return escaped


def fanout_power(board, net_by_name) -> None:
    """Connect surface-mount rail pads to their dedicated internal planes."""
    rail_names = {Net.GROUND, Net.FIVE_VOLTS, Net.THREE_VOLTS_THREE}
    for module in board.GetFootprints():
        for pad in module.Pads():
            name = pad.GetNetname()
            if (
                pad.GetAttribute() != pcbnew.PAD_ATTRIB_SMD
                or name not in rail_names
            ):
                continue
            at = pad.GetPosition()
            escaped = _power_escape_position(module, pad)
            net = net_by_name[name]
            kicad.add_trace(board, net, at, escaped)
            kicad.add_via(board, net, escaped)
