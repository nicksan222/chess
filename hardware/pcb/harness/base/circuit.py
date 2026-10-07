"""The single, typed entry point for describing a board and its checks."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Concatenate, cast

from .circuit_check import CircuitCheck
from .component import RegisteredComponent
from .connections import NetConnection
from .net import Net
from .pcbnew.layout import BoardLayout
from .pcbnew.outline import BoardOutline
from .pcbnew.route import Trace, Via
from .registry import BoardRegistry


class Circuit[BoardNet: Net](BoardRegistry):
    """Collect placed components and named electrical checks for one board.

    The board's ``net_type`` is an enum defined by its author; it is the one
    vocabulary accepted by every component, route and check. ``place`` passes
    this registry to a component constructor, so the constructor's normal type
    checking remains active while callers never pass a registry themselves.
    ``check`` groups one simulation scenario's stimuli and expectations in a
    readable block. An outline, land patterns on placed parts, traces and vias
    provide the physical facts needed by ``write_board``.
    """

    def __init__(
        self, net_type: type[BoardNet], *, outline: BoardOutline | None = None
    ) -> None:
        """Start a board whose connections all use the same named net vocabulary."""
        if not isinstance(cast(object, net_type), type) or not issubclass(
            net_type, Net
        ):  # pyright: ignore[reportUnnecessaryIsInstance]
            raise ValueError("circuit needs a Net enum type")
        if not tuple(net_type):
            raise ValueError("circuit needs a nonempty Net enum type")
        if len(net_type.__members__) != len(tuple(net_type)):
            raise ValueError("circuit Net enum has duplicate net labels")
        if outline is not None and not isinstance(cast(object, outline), BoardOutline):
            raise ValueError("circuit outline must be a BoardOutline")
        super().__init__(outline=outline)
        self.net_type = net_type
        self.layout: BoardLayout[BoardNet] = BoardLayout()
        self._traces: list[Trace[BoardNet]] = []
        self._vias: list[Via[BoardNet]] = []

    @property
    def outline(self) -> BoardOutline | None:
        """Return the one board boundary owned by this circuit's registry."""
        return self._physical_outline

    def trace(self, route: Trace[BoardNet]) -> Trace[BoardNet]:
        """Register one intentional copper segment on a named board net."""
        if type(route.net) is not self.net_type:
            raise ValueError("trace must use the board Net enum")
        self._traces.append(route)
        return route

    def via(self, route: Via[BoardNet]) -> Via[BoardNet]:
        """Register one plated connection between the top and bottom copper."""
        if type(route.net) is not self.net_type:
            raise ValueError("via must use the board Net enum")
        self._vias.append(route)
        return route

    def traces(self) -> tuple[Trace[BoardNet], ...]:
        """Expose a stable snapshot of declared trace segments."""
        return tuple(self._traces)

    def vias(self) -> tuple[Via[BoardNet], ...]:
        """Expose a stable snapshot of declared vias."""
        return tuple(self._vias)

    def write_board(self, path: Path) -> Path:
        """Render and save the declaration as a KiCad board file.

        This is the authoring boundary where typed nets and abstract placement
        become native ``pcbnew`` objects. The circuit must have a board outline
        and every placed component must provide a land pattern; validation here
        checks declared geometry and topology before serialization. Saving does
        not run KiCad ERC/DRC, autoroute copper, or prove a manufactured board.
        """
        from .pcbnew.render.board import write_board

        return write_board(self, path)

    def write_project(self, directory: Path, name: str) -> Path:
        """Create a board-only KiCad project from this one circuit declaration.

        Returns the project file path. The new directory contains a KiCad
        project and board; a schematic is not inferred from physical pads.
        """
        from .pcbnew.render.project import write_project

        return write_project(self, directory, name)

    def register_component(self, component: RegisteredComponent) -> None:
        """Reject foreign nets before a component enters this circuit."""
        for _, connection in component.pin_connections():
            if (
                isinstance(connection, NetConnection)
                and type(connection.net) is not self.net_type
            ):
                raise ValueError("component connection must use the board Net enum")
        super().register_component(component)

    def place[**Args, Part: RegisteredComponent](
        self,
        constructor: Callable[Concatenate[BoardRegistry, Args], Part],
        /,
        *args: Args.args,
        **kwargs: Args.kwargs,
    ) -> Part:
        """Construct, check clearance, and register one precisely typed part.

        When this circuit has an outline, registration checks the new
        courtyard against the board edge and existing components. A failure
        leaves the registry unchanged, so no later manual placement check is
        needed before rendering the board.
        """
        part = constructor(self, *args, **kwargs)
        if not any(known is part for known in self.components()):
            raise ValueError("component constructor did not register its result")
        return part

    def check(
        self,
        name: str,
        *,
        ground: BoardNet,
        purpose: str,
        components: tuple[RegisteredComponent, ...] | None = None,
    ) -> CircuitCheck[BoardNet]:
        """Begin one named electrical check with its conditions and expectations."""
        if type(ground) is not self.net_type:
            raise ValueError("check ground must use the board Net enum")
        return CircuitCheck(self, name, ground, purpose, components)

    def deck(self, check_name: str) -> str:
        """Render the selected check to ngspice text without exposing its syntax."""
        from .spice.render.deck import render_deck

        self._require_check(check_name)
        return render_deck(self, check_name)

    def run(self, check_name: str, *, output: Path | None = None) -> dict[str, float]:
        """Run the selected check with ngspice and return measured values."""
        from .spice.render.run import run_deck

        self._require_check(check_name)
        return run_deck(self, check_name, output=output)

    def _require_check(self, name: str) -> None:
        """Translate an internal scenario lookup into the public check language."""
        try:
            self.scenario(name)
        except ValueError as error:
            raise ValueError(f"unknown circuit check: {name}") from error
