"""Python DSL for physical piece-presence simulation cases."""

from __future__ import annotations

from dataclasses import dataclass, replace


@dataclass(frozen=True)
class SensorEvent:
    at_ms: float
    square: str
    occupied: bool


@dataclass(frozen=True)
class SensorCheck:
    name: str
    at_ms: float
    square: str
    occupied: bool


@dataclass(frozen=True)
class MovementCase:
    """Ordered physical actions plus an explicit registry of voltage checks."""

    name: str
    initially_occupied: frozenset[str] = frozenset()
    events: tuple[SensorEvent, ...] = ()
    checks: tuple[SensorCheck, ...] = ()

    def starts_with(self, *squares: str) -> MovementCase:
        return replace(self, initially_occupied=frozenset(squares))

    def lift(self, square: str, at_ms: float) -> MovementCase:
        return self._event(square, at_ms, occupied=False)

    def place(self, square: str, at_ms: float) -> MovementCase:
        return self._event(square, at_ms, occupied=True)

    def expect_occupied(self, name: str, square: str, at_ms: float) -> MovementCase:
        return self._check(name, square, at_ms, occupied=True)

    def expect_empty(self, name: str, square: str, at_ms: float) -> MovementCase:
        return self._check(name, square, at_ms, occupied=False)

    def _event(self, square: str, at_ms: float, *, occupied: bool) -> MovementCase:
        if at_ms <= 0 or (self.events and at_ms <= self.events[-1].at_ms):
            raise ValueError(f"{self.name}: sensor event times must increase")
        return replace(
            self, events=(*self.events, SensorEvent(at_ms, square, occupied))
        )

    def _check(
        self, name: str, square: str, at_ms: float, *, occupied: bool
    ) -> MovementCase:
        if not name or any(check.name == name for check in self.checks):
            raise ValueError(f"{self.name}: check names must be non-empty and unique")
        return replace(
            self,
            checks=(*self.checks, SensorCheck(name, at_ms, square, occupied)),
        )
