"""Assign collision-free ngspice node names to human board net names."""

from __future__ import annotations

from typing import cast

from ...net import Net


class NodeMap:
    """Translate design net names without assuming they are SPICE-safe tokens.

    ngspice reserves node ``0`` for ground. Every other net gets a stable ``n1``,
    ``n2`` and so on, ordered by its human name. This avoids collisions such as
    ``A-B`` and ``A_B`` both becoming ``a_b`` after punctuation removal.
    """

    def __init__(self, nets: tuple[Net, ...], ground_net: Net) -> None:
        """Create one mapping and require that ground is a real design net."""
        if not isinstance(cast(object, ground_net), Net) or any(
            not isinstance(cast(object, net), Net) for net in nets
        ):
            raise ValueError("node map needs Net enum members")
        if any(type(net) is not type(ground_net) for net in nets):
            raise ValueError("node map needs one Net enum type")
        unique = set(nets)
        if ground_net not in unique:
            raise ValueError(f"unknown ground net: {ground_net.label}")
        self._nodes = {ground_net: "0"}
        self._nodes.update(
            {
                name: f"n{index}"
                for index, name in enumerate(
                    sorted(
                        unique - {ground_net},
                        key=lambda net: (type(net).__name__, net.label),
                    ),
                    1,
                )
            }
        )

    def node(self, net: Net) -> str:
        """Return the simulator node for a known design net."""
        try:
            return self._nodes[net]
        except KeyError as error:
            raise ValueError(f"unknown net: {net}") from error

    def comments(self) -> tuple[str, ...]:
        """Return a readable legend for debugging a generated circuit."""
        return tuple(
            f"* net {net.label}: {node}"
            for net, node in sorted(
                self._nodes.items(),
                key=lambda item: (type(item[0]).__name__, item[0].label),
            )
        )
