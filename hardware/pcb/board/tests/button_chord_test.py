"""Independent button lines must remain independent during overlapping presses."""

import pytest

from pcb.board.board import Board, BoardNet
from pcb.harness import StateChange
from shared.electronics.tactile_switch import TactileSwitchPin


@pytest.mark.parametrize("pressed", [("UP", "LEFT", "OK"), ("RESET", "PASS", "F5")])
def test_three_buttons_then_release_only_one(pressed: tuple[str, str, str]) -> None:
    board = Board()
    with board.check(
        "three_buttons",
        ground=BoardNet.GROUND,
        components=tuple(board.buttons.values()),
        purpose="Three simultaneous presses, followed by releasing only one",
    ) as check:
        check.transient(duration_seconds=0.04, step_seconds=0.0001)
        for name, button in board.buttons.items():
            check.dc_supply(
                f"Vpull_{name}",
                BoardNet(button.net(TactileSwitchPin.SIGNAL)),
                BoardNet.GROUND,
                volts=3.3,
                output_resistance_ohms=50_000,
            )
            changes = ()
            if name in pressed:
                changes = (StateChange(0.01, True),)
            if name == pressed[0]:
                changes += (StateChange(0.03, False),)
            check.drive_state(button, initial=False, changes=changes)
            for seconds, active in (
                (0.005, False),
                (0.02, name in pressed),
                (0.035, name in pressed[1:]),
            ):
                check.voltage_at(
                    button,
                    TactileSwitchPin.SIGNAL,
                    between=(0, 0.1) if active else (3.2, 3.3),
                    at_seconds=seconds,
                    because=f"{name} is {'pressed' if active else 'released'}",
                )
    board.run("three_buttons")


def test_all_buttons_can_be_pressed_without_a_shared_input() -> None:
    board = Board()
    with board.check(
        "all_buttons",
        ground=BoardNet.GROUND,
        components=tuple(board.buttons.values()),
        purpose="All buttons pressed together",
    ) as check:
        for name, button in board.buttons.items():
            supply = check.dc_supply(
                f"Vpull_{name}",
                BoardNet(button.net(TactileSwitchPin.SIGNAL)),
                BoardNet.GROUND,
                volts=3.3,
                output_resistance_ohms=50_000,
            )
            check.drive_state(button, initial=True)
            check.voltage_at(
                button,
                TactileSwitchPin.SIGNAL,
                between=(0, 0.1),
                because=f"{name} reaches a low input level",
            )
            check.source_current(
                supply,
                between=(-67e-6, -65e-6),
                because="Each external pull-up supplies its own closed contact",
            )
    board.run("all_buttons")
