"""Render on/off environmental stimuli used by switch-based models."""

from ..state import ComponentState
from .number import spice_number


def render_state(reference: str, state: ComponentState | None) -> str:
    initial = state.initial if state else False
    changes = state.changes if state else ()
    source = f"Vstate_{reference} state_{reference} 0"
    if not changes:
        return f"{source} DC {int(initial)}"
    points = [f"0 {int(initial)}"]
    previous = initial
    previous_seconds = 0.0
    for change in changes:
        edge = min(1e-12, (change.seconds - previous_seconds) / 2)
        points.extend(
            (
                f"{spice_number(change.seconds - edge)} {int(previous)}",
                f"{spice_number(change.seconds)} {int(change.active)}",
            )
        )
        previous = change.active
        previous_seconds = change.seconds
    return f"{source} PWL({' '.join(points)})"
