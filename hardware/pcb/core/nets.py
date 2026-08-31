"""Which net each pad belongs to.

The schematic publishes nets as lists of (reference, pin) pairs. Copper needs the
inverse: given a pad, what net is it on. That answer decides whether the ground
pour connects to a pad or has to be cleared away from it, which is the difference
between a working board and one with every net shorted together.
"""

from __future__ import annotations

from core import sources

GROUND_NET = "GND"
SUPPLY_NET = "+5V"
LOGIC_SUPPLY_NET = "+3V3"


def pad_nets() -> dict[tuple[str, str], str]:
    """Map (reference, pin) to net name."""
    netlist = sources.netlist()
    mapping: dict[tuple[str, str], str] = {}
    for net, nodes in netlist["nets"].items():
        for reference, pin in nodes:
            key = (reference, pin)
            if key in mapping and mapping[key] != net:
                raise RuntimeError(
                    f"{reference} pin {pin} is on two nets: {mapping[key]} and {net}"
                )
            mapping[key] = net
    return mapping


def net_pads() -> dict[str, set[tuple[str, str]]]:
    """Map net name to the set of pads on it."""
    netlist = sources.netlist()
    return {
        net: {(reference, pin) for reference, pin in nodes}
        for net, nodes in netlist["nets"].items()
    }


def is_ground(net: str | None) -> bool:
    return net == GROUND_NET
