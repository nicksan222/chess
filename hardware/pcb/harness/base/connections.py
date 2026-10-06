"""Typed descriptions of intended electrical connections between component pins."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

from .net import Net


@dataclass(frozen=True, slots=True, order=True)
class Endpoint:
    """The identity of one pin on one placed component, such as ``U5/14``.

    ``reference`` identifies the component instance. ``pin`` is the pin number
    printed on its datasheet or connector drawing. An endpoint does not own a
    net: the component's pin map owns that decision.
    """

    reference: str
    pin: str

    def __post_init__(self) -> None:
        """Prevent references to unnamed components or pins."""
        if not self.reference.strip() or not self.pin.strip():
            raise ValueError("endpoint needs a reference and pin")


@dataclass(frozen=True, slots=True)
class NetConnection:
    """Say that a pin must join a named electrical network.

    Pins declaring the same ``net`` are intended to connect. Optional ``peers``
    demand that particular other pins also declare this network. A peer is a
    check of design intent; it does not create a second assignment or a track.
    The renderer later turns the shared net into a native PCB net and only
    explicit ``Trace``/``Via`` declarations become copper.
    """

    net: Net
    peers: tuple[Endpoint, ...] = ()

    def __post_init__(self) -> None:
        """Require a named net and distinct exact-peer requirements."""
        if not isinstance(cast(object, self.net), Net):
            raise ValueError("connected pin needs a Net enum member")
        if len(set(self.peers)) != len(self.peers):
            raise ValueError("connection peers must be unique")


@dataclass(frozen=True, slots=True)
class NoConnect:
    """Say that a real physical pin is intentionally left electrically open.

    This differs from forgetting a pin in the map, which is rejected. The
    reason tells a reviewer why leaving it open is correct for this instance.
    """

    reason: str

    def __post_init__(self) -> None:
        """Make each unused-pin decision reviewable."""
        if not self.reason.strip():
            raise ValueError("no-connect needs a reason")


type PinConnection = NetConnection | NoConnect
