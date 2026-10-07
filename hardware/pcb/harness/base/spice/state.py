"""Physical on/off stimuli for component models, without simulator syntax."""

import math
from dataclasses import dataclass
from itertools import pairwise


@dataclass(frozen=True, slots=True)
class StateChange:
    seconds: float
    active: bool

    def __post_init__(self) -> None:
        if not math.isfinite(self.seconds) or self.seconds <= 0:
            raise ValueError("state change needs a positive finite time")
        if type(self.active) is not bool:
            raise ValueError("component state must be boolean")


@dataclass(frozen=True, slots=True)
class ComponentState:
    reference: str
    initial: bool
    changes: tuple[StateChange, ...] = ()

    def __post_init__(self) -> None:
        if type(self.initial) is not bool:
            raise ValueError("component state must be boolean")
        times = tuple(change.seconds for change in self.changes)
        if any(later <= earlier for earlier, later in pairwise(times)):
            raise ValueError("component state times must increase")
