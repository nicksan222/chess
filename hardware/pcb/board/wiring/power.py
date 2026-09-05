"""Native KiCad routing and plane fanout for board power."""

from __future__ import annotations

from collections.abc import Mapping

from board.wiring.context import WiringContext, WiringStage
from board.wiring.nets import Net
from components import catalog
from components.barrel_jack import DC_INPUT_JACK, BarrelJackPin
from components.fuse import INPUT_FUSE, FusePin
from components.power_switch import MAIN_POWER_SWITCH, PowerSwitchPin
from components.raspberry_pi_header import RaspberryPiHeader
from domain import rules
from domain.component import ComponentReference
from domain.connectivity import EndpointKey
from kicad import board as kicad
from kicad.api import pcbnew


class InputPowerWiring(WiringStage):
    """Route protected input current around jack contacts and signal lanes."""

    def route(self) -> None:
        board, net_by_name, pads = (
            self.context.board,
            self.context.nets,
            self.context.pads,
        )
        routes = (
            (
                Net.DC_INPUT,
                DC_INPUT_JACK.endpoint(BarrelJackPin.CENTRE_POSITIVE),
                INPUT_FUSE.endpoint(FusePin.UNFUSED_INPUT),
                # Run below the rotated PJ-102A body; its offset grounded slot sits
                # above the centre-positive terminal.
                -183.0,
            ),
            (
                Net.DC_FUSED,
                INPUT_FUSE.endpoint(FusePin.FUSED_OUTPUT),
                MAIN_POWER_SWITCH.endpoint(PowerSwitchPin.FUSED_INPUT),
                -194.0,
            ),
        )
        for name, left, right, lane_y in routes:
            net = net_by_name[name]
            start, end = pads[left].GetPosition(), pads[right].GetPosition()
            native_y = kicad.point(0.0, lane_y).y
            first = pcbnew.VECTOR2I(start.x, native_y)
            second = pcbnew.VECTOR2I(end.x, native_y)
            kicad.add_trace(board, net, start, first, width=rules.POWER_TRACE_WIDTH_MM)
            kicad.add_trace(board, net, first, second, width=rules.POWER_TRACE_WIDTH_MM)
            kicad.add_trace(board, net, second, end, width=rules.POWER_TRACE_WIDTH_MM)


class PowerFanoutWiring(WiringStage):
    """Connect SMD rail pads to dedicated internal planes before signals."""

    def route(self) -> None:
        board, net_by_name = self.context.board, self.context.nets
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


def _power_escape_position(
    module: pcbnew.FOOTPRINT, pad: pcbnew.PAD
) -> pcbnew.VECTOR2I:
    """Choose a short fanout that clears its package and nearby signal lanes."""
    at = pad.GetPosition()
    centre = module.GetPosition()
    dx, dy = at.x - centre.x, at.y - centre.y
    reference = module.GetReference()

    if reference == ComponentReference.HOST_GPIO_HEADER:
        escape_mm, horizontal = RaspberryPiHeader.POWER_ESCAPE_MM, True
    else:
        escape_mm, horizontal = catalog.power_escape_policy(
            module.GetValue(), pad.GetNumber()
        )
    distance = pcbnew.FromMM(escape_mm)
    if horizontal:
        escaped = pcbnew.VECTOR2I(
            at.x + (distance if dx >= 0 else -distance),
            at.y,
        )
    else:
        length = max(1, round((dx * dx + dy * dy) ** 0.5))
        escaped = pcbnew.VECTOR2I(
            at.x + dx * distance // length,
            at.y + dy * distance // length,
        )
    return escaped


def route_input_power(
    board: pcbnew.BOARD,
    net_by_name: Mapping[str, pcbnew.NETINFO_ITEM],
    pads: Mapping[EndpointKey, pcbnew.PAD],
) -> None:
    """Compatibility entry point for protected input wiring."""
    InputPowerWiring(WiringContext(board, net_by_name, pads)).route()


def fanout_power(
    board: pcbnew.BOARD, net_by_name: Mapping[str, pcbnew.NETINFO_ITEM]
) -> None:
    """Compatibility entry point for plane fanout."""
    PowerFanoutWiring(WiringContext(board, net_by_name, {})).route()
