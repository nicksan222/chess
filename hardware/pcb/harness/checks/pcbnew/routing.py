"""Require physical copper inputs before deriving routed SPICE models."""

import pcbnew

from pcb.harness.base.spice.render.program import SimulationUnavailable


def require_routed_copper(board: pcbnew.BOARD, plane_nets: tuple[str, ...]) -> None:
    """An absent route or plane is unavailable data, never a zero-ohm model."""
    if not tuple(board.GetTracks()):
        raise SimulationUnavailable(
            "the new board has no routed copper; routing-dependent SPICE checks are blocked"
        )
    zones = {zone.GetNetname(): zone for zone in board.Zones()}
    for net in plane_nets:
        zone = zones.get(net)
        if zone is None or zone.GetFilledPolysList(zone.GetLayer()).Area() <= 0:
            raise SimulationUnavailable(f"the new board has no filled {net} plane")
