"""Button contact bridges and header launch/fallback routing policy."""

from __future__ import annotations

from collections.abc import Mapping

from base.component import ComponentReference
from base.connectivity import ConnectionGraph, EndpointKey
from base.kicad import board as kicad
from base.kicad import grid_router
from base.kicad.api import pcbnew
from board.wiring import common
from board.wiring.context import WiringContext, WiringStage
from board.wiring.nets import ButtonNet
from components.tactile_switch import TactileSwitchPad


class ButtonWiring(WiringStage):
    """Connect duplicate contacts, then try surface and internal launch lanes."""

    def route(self) -> None:
        board, net_by_name, pads = (
            self.context.board,
            self.context.nets,
            self.context.pads,
        )
        names = (
            ButtonNet.F3,
            ButtonNet.F4,
            ButtonNet.F5,
            ButtonNet.RESET,
            ButtonNet.PASS,
            ButtonNet.F1,
            ButtonNet.F2,
            ButtonNet.OK,
            ButtonNet.RIGHT,
            ButtonNet.LEFT,
            ButtonNet.DOWN,
            ButtonNet.UP,
        )
        for index, name in enumerate(names):
            nodes = list(self.context.connection(name).endpoints)
            pi = next(
                node for node in nodes if node[0] == ComponentReference.HOST_GPIO_HEADER
            )
            switch_node = next(node for node in nodes if node[0].startswith("SW"))
            module = common.footprint(board, switch_node[0])
            primary = next(
                pad
                for pad in module.Pads()
                if pad.GetNumber() == TactileSwitchPad.SIGNAL_PRIMARY
            )
            duplicate = next(
                pad
                for pad in module.Pads()
                if pad.GetNumber() == TactileSwitchPad.SIGNAL_DUPLICATE
            )
            net = net_by_name[name]
            kicad.add_trace(
                board,
                net,
                primary.GetPosition(),
                duplicate.GetPosition(),
                pcbnew.B_Cu,
            )
            try:
                route = common.find_route(
                    board,
                    net,
                    pads[pi].GetPosition(),
                    primary.GetPosition(),
                    preferred_layer_index=1 - index % 2,
                )
            except RuntimeError:
                fallback_layers = {
                    ButtonNet.F1: pcbnew.In4_Cu,
                    ButtonNet.LEFT: pcbnew.In4_Cu,
                    ButtonNet.OK: pcbnew.In5_Cu,
                    ButtonNet.DOWN: pcbnew.In5_Cu,
                    ButtonNet.F3: pcbnew.In6_Cu,
                    ButtonNet.RIGHT: pcbnew.In6_Cu,
                }
                signal_layers = (pcbnew.In4_Cu, pcbnew.In5_Cu, pcbnew.In6_Cu)
                preferred = fallback_layers.get(
                    name, signal_layers[index % len(signal_layers)]
                )
                candidates = (preferred,) + tuple(
                    layer for layer in signal_layers if layer != preferred
                )
                start = pads[pi].GetPosition()
                header = common.footprint(board, ComponentReference.HOST_GPIO_HEADER)
                direction = 1 if start.y > header.GetPosition().y else -1
                launch = pcbnew.VECTOR2I(
                    start.x
                    + pcbnew.FromMM(0.8 if name == ButtonNet.F3 or index % 2 else -0.8),
                    start.y + direction * pcbnew.FromMM(4.5),
                )
                for layer in candidates:
                    try:
                        route = common.find_route(
                            board,
                            net,
                            launch,
                            primary.GetPosition(),
                            preferred_layer_index=0,
                            allow_vias=False,
                            layers=(layer,),
                            diagonals=True,
                        )
                        break
                    except RuntimeError:
                        continue
                else:
                    raise RuntimeError(f"no internal button route for {name}")
                kicad.add_trace(board, net, start, launch, layer)
                grid_router.apply_route(
                    board, net, launch, primary.GetPosition(), route
                )
            else:
                grid_router.apply_route(
                    board, net, pads[pi].GetPosition(), primary.GetPosition(), route
                )


def route_buttons(
    board: pcbnew.BOARD,
    net_by_name: Mapping[str, pcbnew.NETINFO_ITEM],
    pads: Mapping[EndpointKey, pcbnew.PAD],
    graph: ConnectionGraph,
) -> None:
    """Compatibility entry point; new pipelines compose ``ButtonWiring``."""
    ButtonWiring(WiringContext(board, net_by_name, pads, graph)).route()
