"""Tests that characterise a known residual failure (pushback-final, S6c).

A residual test passes while the board still fails in a recorded way, within
recorded bounds: it stops the residual getting worse; it is not evidence of a
correct behaviour. `@residual("<ASSUMPTION>")` ties the test to the verification
ASSUMPTION that records the residual (an unknown name fails at import), and
`pcb.build` lists every marked test under "Known residuals" in review.md, read
from the test sources, so "N tests OK" is never read as N correct behaviours.
"""

from collections.abc import Callable

from pcb.definition.verification import ASSUMPTIONS

RESIDUAL_ATTRIBUTE = "residual_assumption"


def residual[T: Callable[..., object]](assumption: str) -> Callable[[T], T]:
    """Mark a test as recording a known residual that belongs to a verification ASSUMPTION.

    Raises if `assumption` is not a key of `ASSUMPTIONS`, so a residual cannot point at an entry
    that was removed.
    """
    if assumption not in ASSUMPTIONS:
        raise KeyError(f"residual names no verification ASSUMPTION: {assumption}")

    def mark(test: T) -> T:
        setattr(test, RESIDUAL_ATTRIBUTE, assumption)
        return test

    return mark
