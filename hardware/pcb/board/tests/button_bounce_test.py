"""A prescribed bouncing contact reaches the input without affecting neighbors.

The 10–100 kΩ external biases are test conditions, not guaranteed Pi pull-up
limits. Contact bounce is injected explicitly; firmware debounce is not modeled.
"""

import pytest

from pcb.board.board import Board, BoardNet
from pcb.harness import StateChange
from shared.electronics.tactile_switch import TactileSwitchPin


@pytest.mark.parametrize("pullup_ohms", [10_000.0, 50_000.0, 100_000.0])
def test_bounce_then_held_press_then_release(pullup_ohms: float) -> None:
    board = Board()
    with board.check(
        "button_bounce",
        ground=BoardNet.GROUND,
        components=tuple(board.buttons.values()),
        purpose="OK bounces, settles pressed, then releases; other inputs remain high",
    ) as check:
        check.transient(duration_seconds=0.04, step_seconds=0.00005)
        for name, button in board.buttons.items():
            check.dc_supply(
                f"Vpull_{name}",
                BoardNet(button.net(TactileSwitchPin.SIGNAL)),
                BoardNet.GROUND,
                volts=3.3,
                output_resistance_ohms=pullup_ohms,
            )
            if name == "OK":
                check.drive_state(
                    button,
                    initial=False,
                    changes=(
                        StateChange(0.01, True),
                        StateChange(0.011, False),
                        StateChange(0.012, True),
                        StateChange(0.013, False),
                        StateChange(0.014, True),
                        StateChange(0.03, False),
                    ),
                )
            for seconds, contact_closed in (
                (0.005, False),
                (0.0105, True),
                (0.0115, False),
                (0.0125, True),
                (0.0135, False),
                (0.02, True),
                (0.035, False),
            ):
                active = name == "OK" and contact_closed
                check.voltage_at(
                    button,
                    TactileSwitchPin.SIGNAL,
                    between=(0, 0.1) if active else (3.2, 3.3),
                    at_seconds=seconds,
                    because=f"{name} follows its own contact at {seconds}s",
                )
    board.run("button_bounce")
