"""Readable conditions and expected results for one circuit check."""

from __future__ import annotations

from enum import StrEnum
from typing import TYPE_CHECKING, Self

from .component import BoardComponent, RegisteredComponent
from .connections import Endpoint
from .net import Net
from .spice.analysis import AcSweep, Analysis, OperatingPoint, Transient
from .spice.measurement import (
    CurrentThrough,
    Limit,
    Observation,
    SpiceRequirement,
    VoltageAt,
    VoltageBetween,
)
from .spice.model import ModelOverride, ModelParameter
from .spice.scenario import SpiceScenario
from .spice.source import CurrentSource, DcVoltage, PulseVoltage, Source, VoltageSource
from .spice.state import ComponentState, StateChange

if TYPE_CHECKING:
    from .circuit import Circuit


class CircuitCheck[BoardNet: Net]:
    """A staged set of conditions and assertions for one electrical experiment.

    Use as a context manager. A clean exit registers the complete setup and all
    expectations together; an exception leaves the board untouched. The public
    methods say what to drive and observe, while internal SPICE classes decide
    how to express those choices to the simulator. The default analysis is a
    settled DC operating point; call ``transient`` or ``ac_sweep`` before an
    expectation to ask a different question. A passing assertion proves only
    that the selected simulator model produced a value in its declared band.
    """

    def __init__(
        self,
        board: Circuit[BoardNet],
        name: str,
        ground: BoardNet,
        purpose: str,
        components: tuple[RegisteredComponent, ...] | None = None,
    ) -> None:
        """Hold a check until its context exits successfully."""
        self._board = board
        self._name = name
        self._ground = ground
        self._purpose = purpose
        self._analysis: Analysis = OperatingPoint()
        self._sources: list[Source] = []
        self._expectations: list[tuple[str | None, SpiceRequirement]] = []
        self._closed = False
        self._components = board.components() if components is None else components
        if (components is not None and not self._components) or len(
            {part.reference for part in self._components}
        ) != len(self._components):
            raise ValueError("check needs a nonempty unique component selection")
        if any(
            not any(known is part for known in board.components())
            for part in self._components
        ):
            raise ValueError("check components must belong to this circuit")
        self._scoped = components is not None
        self._states: list[ComponentState] = []
        self._model_overrides: list[ModelOverride] = []

    @property
    def _selected_components(self) -> tuple[RegisteredComponent, ...]:
        return self._components if self._scoped else self._board.components()

    def parameter(
        self, component: RegisteredComponent, name: str, *, value: float
    ) -> None:
        """Set one numeric model corner for this check; nominal facts stay intact."""
        self._ensure_open()
        if not any(known is component for known in self._selected_components):
            raise ValueError("parameter corner needs a selected component")
        model = component.simulation_model()
        parameter = (
            next(
                (parameter for parameter in model.parameters if parameter.name == name),
                None,
            )
            if model
            else None
        )
        if parameter is None:
            raise ValueError(f"{component.reference}: unknown model parameter {name}")
        if any(
            override.reference == component.reference
            and override.parameter.name == name
            for override in self._model_overrides
        ):
            raise ValueError("duplicate model parameter corner")
        self._model_overrides.append(
            ModelOverride(
                component.reference, ModelParameter(name, value, parameter.unit)
            )
        )

    def drive_state(
        self,
        component: RegisteredComponent,
        *,
        initial: bool,
        changes: tuple[StateChange, ...] = (),
    ) -> None:
        """Apply physical on/off events to a selected component's model."""
        self._ensure_open()
        if not any(known is component for known in self._selected_components):
            raise ValueError("state stimulus needs a selected component")
        if any(state.reference == component.reference for state in self._states):
            raise ValueError("duplicate component state stimulus")
        model = component.simulation_model()
        if model is None or model.key not in {"open_drain_sensor", "button_contact"}:
            raise ValueError("component model does not support on/off stimuli")
        self._states.append(ComponentState(component.reference, initial, changes))

    def __enter__(self) -> Self:
        """Allow a readable ``with board.check(...) as check`` block."""
        if self._closed:
            raise ValueError("check is already closed")
        return self

    def __exit__(
        self, exception_type: object, exception: object, traceback: object
    ) -> None:
        """Commit only a block that completed without an exception."""
        self._closed = True
        if exception_type is None:
            self._commit()

    def transient(self, *, duration_seconds: float, step_seconds: float) -> None:
        """Observe the circuit from startup through a finite time interval."""
        self._ensure_open()
        self._ensure_analysis_precedes_expectations()
        self._analysis = Transient(duration_seconds, step_seconds)

    def ac_sweep(
        self, *, start_hz: float, stop_hz: float, points_per_decade: int
    ) -> None:
        """Observe small-signal response over a frequency range."""
        self._ensure_open()
        self._ensure_analysis_precedes_expectations()
        self._analysis = AcSweep(start_hz, stop_hz, points_per_decade)

    def dc_supply(
        self,
        name: str,
        positive: BoardNet,
        negative: BoardNet,
        *,
        volts: float,
        ac_volts: float | None = None,
        output_resistance_ohms: float = 0.0,
    ) -> VoltageSource:
        """Drive a fixed voltage, optionally through a declared source resistance."""
        self._ensure_open()
        if (
            type(positive) is not self._board.net_type
            or type(negative) is not self._board.net_type
        ):
            raise ValueError("supply must use the board Net enum")
        source = VoltageSource(
            name, positive, negative, DcVoltage(volts), ac_volts, output_resistance_ohms
        )
        self._sources.append(source)
        return source

    def pulse_supply(
        self,
        name: str,
        positive: BoardNet,
        negative: BoardNet,
        *,
        low_volts: float,
        high_volts: float,
        delay_seconds: float,
        rise_seconds: float,
        fall_seconds: float,
        high_seconds: float,
        period_seconds: float,
    ) -> VoltageSource:
        """Drive a repeating low-to-high voltage for a time-domain check."""
        self._ensure_open()
        if (
            type(positive) is not self._board.net_type
            or type(negative) is not self._board.net_type
        ):
            raise ValueError("supply must use the board Net enum")
        waveform = PulseVoltage(
            low_volts,
            high_volts,
            delay_seconds,
            rise_seconds,
            fall_seconds,
            high_seconds,
            period_seconds,
        )
        source = VoltageSource(name, positive, negative, waveform)
        self._sources.append(source)
        return source

    def inject_current(
        self, name: str, from_net: BoardNet, to_net: BoardNet, *, amperes: float
    ) -> None:
        """Force a signed current between two nets as a simulation stimulus."""
        self._ensure_open()
        if (
            type(from_net) is not self._board.net_type
            or type(to_net) is not self._board.net_type
        ):
            raise ValueError("current injection must use the board Net enum")
        self._sources.append(CurrentSource(name, from_net, to_net, amperes))

    def voltage_at[Pin: StrEnum](
        self,
        component: BoardComponent[Pin],
        pin: Pin,
        *,
        between: tuple[float, float],
        because: str,
        at_seconds: float | None = None,
    ) -> None:
        """Require one component pin's ground-relative voltage in a pass band."""
        self._ensure_open()
        if not any(known is component for known in self._selected_components):
            raise ValueError("voltage check needs a component on this board")
        if not isinstance(pin, component.definition.pin_type):
            raise ValueError("voltage check pin must belong to the component kind")
        requirement = SpiceRequirement(
            self._name,
            VoltageAt(Endpoint(component.reference, str(pin))),
            self._observation(),
            Limit(*between),
            because,
            at_seconds,
        )
        self._expectations.append((component.reference, requirement))

    def voltage_between[PositivePin: StrEnum, NegativePin: StrEnum](
        self,
        positive_component: BoardComponent[PositivePin],
        positive_pin: PositivePin,
        negative_component: BoardComponent[NegativePin],
        negative_pin: NegativePin,
        *,
        between: tuple[float, float],
        because: str,
    ) -> None:
        """Require the first pin minus the second pin to lie in a voltage band."""
        self._ensure_open()
        for component, pin in (
            (positive_component, positive_pin),
            (negative_component, negative_pin),
        ):
            if not any(known is component for known in self._board.components()):
                raise ValueError("voltage check needs a component on this board")
            if not isinstance(pin, component.definition.pin_type):
                raise ValueError("voltage check pin must belong to the component kind")
        requirement = SpiceRequirement(
            self._name,
            VoltageBetween(
                Endpoint(positive_component.reference, str(positive_pin)),
                Endpoint(negative_component.reference, str(negative_pin)),
            ),
            self._observation(),
            Limit(*between),
            because,
        )
        self._expectations.append((positive_component.reference, requirement))

    def source_current(
        self,
        supply: VoltageSource,
        *,
        between: tuple[float, float],
        because: str,
        at_seconds: float | None = None,
    ) -> None:
        """Require the total signed current through this check's voltage supply.

        This is a whole-circuit result. It is not assumed to be the current
        through any one resistor unless the declared topology proves that.
        """
        self._ensure_open()
        if not any(known is supply for known in self._sources):
            raise ValueError("current check needs a supply from this check")
        requirement = SpiceRequirement(
            self._name,
            CurrentThrough(supply.name),
            self._observation(),
            Limit(*between),
            because,
            at_seconds,
        )
        self._expectations.append((None, requirement))

    def _observation(self) -> Observation:
        """Choose one scalar observation suited to the selected analysis."""
        if isinstance(self._analysis, OperatingPoint):
            return Observation.SINGLE
        if isinstance(self._analysis, Transient):
            return Observation.FINAL
        return Observation.MAXIMUM

    def _ensure_analysis_precedes_expectations(self) -> None:
        """Avoid silently changing how an already-declared check is sampled."""
        if self._expectations:
            raise ValueError("choose an analysis before expectations")

    def _ensure_open(self) -> None:
        """Prevent declarations after registration or a failed check block."""
        if self._closed:
            raise ValueError("check is already closed")

    def _commit(self) -> None:
        """Register one complete simulation setup and its assertions."""
        if not self._expectations:
            raise ValueError("electrical check needs at least one expectation")
        for state in self._states:
            if state.changes and (
                not isinstance(self._analysis, Transient)
                or state.changes[-1].seconds > self._analysis.duration_seconds
            ):
                raise ValueError(
                    "state changes need a transient and must fit its duration"
                )
        for _, requirement in self._expectations:
            if requirement.at_seconds is not None and (
                not isinstance(self._analysis, Transient)
                or requirement.at_seconds > self._analysis.duration_seconds
            ):
                raise ValueError(
                    "sample time needs a transient and must fit its duration"
                )
        SpiceScenario(
            self._board,
            self._name,
            self._purpose,
            self._ground,
            self._analysis,
            tuple(self._sources),
            component_references=tuple(
                part.reference for part in self._selected_components
            )
            if self._scoped
            else None,
            states=tuple(self._states),
            model_overrides=tuple(self._model_overrides),
        )
        for reference, requirement in self._expectations:
            if reference is None:
                self._board.register_board_requirement(requirement)
            else:
                self._board.register_requirement(reference, requirement)
