"""Each real button pulls only its assigned GPIO low when pressed."""

import pytest

from pcb.board.board import Board, BoardNet
from shared.electronics.tactile_switch import TactileSwitchPin
from shared.panel_buttons import PANEL_BUTTONS


@pytest.mark.parametrize("pressed", [button.name for button in PANEL_BUTTONS])
def test_press_changes_only_the_assigned_input(pressed: str) -> None:
    board = Board()
    with board.check(
        "button_press",
        ground=BoardNet.GROUND,
        components=tuple(board.buttons.values()),
        purpose=f"Pressing {pressed} leaves every other input high",
    ) as check:
        for name, button in board.buttons.items():
            assert button.net(TactileSwitchPin.SIGNAL) == board.host_header.net(
                PANEL_BUTTONS.by_name(name).header_pin
            )
            check.dc_supply(
                f"Vpull_{name}",
                BoardNet(button.net(TactileSwitchPin.SIGNAL)),
                BoardNet.GROUND,
                volts=3.3,
                output_resistance_ohms=50_000,
            )
            check.drive_state(button, initial=name == pressed)
            check.voltage_at(
                button,
                TactileSwitchPin.SIGNAL,
                between=(0, 0.1) if name == pressed else (3.2, 3.3),
                because=f"{name} is {'pressed' if name == pressed else 'released'}",
            )
    board.run("button_press")
