"""Piece events must reach the right input without changing other squares.

These checks run ngspice with the board's actual Hall sensors, input banks and
bypass capacitors. The component models are ideal sensing/pull-up models; this
does not test magnetic margins, sampled sensor latency or I2C communication.
"""

import unittest
from types import MappingProxyType

from pcb.board.board import Board, BoardNet
from pcb.harness import StateChange

LOGIC_LOW = (0.0, 0.3 * 3.3)
LOGIC_HIGH = (0.7 * 3.3, 3.3)


class PieceDetectionTest(unittest.TestCase):
    def test_each_square_pulls_only_its_own_bank_input_low(self) -> None:
        for occupied_square in Board().sensors:
            with self.subTest(piece_on=occupied_square):
                board = Board()
                with board.check(
                    "one_piece",
                    ground=BoardNet.GROUND,
                    components=board.sensing_components,
                    purpose=f"A piece on {occupied_square} changes only its own bank input",
                ) as check:
                    check.dc_supply(
                        "Vlogic", BoardNet.THREE_VOLTS_THREE, BoardNet.GROUND, volts=3.3
                    )
                    check.drive_state(board.sensors[occupied_square], initial=True)
                    for square in board.sensors:
                        bank, pin = board.sense_input(square)
                        check.voltage_at(
                            bank,
                            pin,
                            between=LOGIC_LOW
                            if square == occupied_square
                            else LOGIC_HIGH,
                            because=f"{square} is {'occupied' if square == occupied_square else 'empty'}",
                        )
                board.run("one_piece")

    def test_placing_then_lifting_a_piece_changes_only_that_square(self) -> None:
        board = Board()
        with board.check(
            "place_and_lift",
            ground=BoardNet.GROUND,
            components=board.sensing_components,
            purpose="Place a piece on A1 at 10 ms, then lift it at 30 ms",
        ) as check:
            check.dc_supply(
                "Vlogic", BoardNet.THREE_VOLTS_THREE, BoardNet.GROUND, volts=3.3
            )
            check.transient(duration_seconds=0.04, step_seconds=0.0001)
            check.drive_state(
                board.sensors["A1"],
                initial=False,
                changes=(StateChange(0.01, True), StateChange(0.03, False)),
            )
            for seconds, piece_present in (
                (0.005, False),
                (0.02, True),
                (0.035, False),
            ):
                for square in board.sensors:
                    bank, pin = board.sense_input(square)
                    check.voltage_at(
                        bank,
                        pin,
                        at_seconds=seconds,
                        between=LOGIC_LOW
                        if square == "A1" and piece_present
                        else LOGIC_HIGH,
                        because=f"At {seconds * 1000:g} ms, only A1 may detect the piece",
                    )
        board.run("place_and_lift")

    def test_moving_a_piece_between_banks_releases_the_old_square(self) -> None:
        board = Board()
        with board.check(
            "move_between_banks",
            ground=BoardNet.GROUND,
            components=board.sensing_components,
            purpose="Move a piece from A1 to H8 at 20 ms",
        ) as check:
            check.dc_supply(
                "Vlogic", BoardNet.THREE_VOLTS_THREE, BoardNet.GROUND, volts=3.3
            )
            check.transient(duration_seconds=0.04, step_seconds=0.0001)
            check.drive_state(
                board.sensors["A1"], initial=True, changes=(StateChange(0.02, False),)
            )
            check.drive_state(
                board.sensors["H8"], initial=False, changes=(StateChange(0.02, True),)
            )
            for seconds, occupied_square in ((0.01, "A1"), (0.03, "H8")):
                for square in board.sensors:
                    bank, pin = board.sense_input(square)
                    check.voltage_at(
                        bank,
                        pin,
                        at_seconds=seconds,
                        between=LOGIC_LOW if square == occupied_square else LOGIC_HIGH,
                        because=f"At {seconds * 1000:g} ms, the piece is on {occupied_square}",
                    )
        board.run("move_between_banks")

    def test_local_bypasses_charge_when_the_logic_supply_rises(self) -> None:
        board = Board()
        capacitance = sum(
            cap.capacitance_farads
            for cap in (*board.sensor_bypasses.values(), *board.bank_bypasses.values())
        )
        charging_current = capacitance * 3.3 / 0.001
        with board.check(
            "power_up_sensing",
            ground=BoardNet.GROUND,
            components=board.sensing_components,
            purpose="The real Hall and bank bypasses load the 3.3 V rail during startup",
        ) as check:
            check.transient(duration_seconds=0.004, step_seconds=0.00001)
            supply = check.pulse_supply(
                "Vlogic",
                BoardNet.THREE_VOLTS_THREE,
                BoardNet.GROUND,
                low_volts=0,
                high_volts=3.3,
                delay_seconds=0.001,
                rise_seconds=0.001,
                fall_seconds=0.001,
                high_seconds=0.01,
                period_seconds=0.02,
            )
            check.source_current(
                supply,
                at_seconds=0.0015,
                between=(-charging_current * 1.02, -charging_current * 0.98),
                because="Charging current is C × dV/dt, plus small modeled input leakage",
            )
        board.run("power_up_sensing")

    def test_swapped_bank_inputs_are_caught_by_the_simulation(self) -> None:
        board = Board()
        bank, expected_pin = board.sense_input("A1")
        _, neighbour_pin = board.sense_input("B1")
        pins = dict(bank.pins)
        pins[expected_pin], pins[neighbour_pin] = (
            pins[neighbour_pin],
            pins[expected_pin],
        )
        object.__setattr__(bank, "pins", MappingProxyType(pins))
        with board.check(
            "miswired_A1",
            ground=BoardNet.GROUND,
            components=board.sensing_components,
            purpose="Negative control: crossed A1/B1 inputs must fail piece detection",
        ) as check:
            check.dc_supply(
                "Vlogic", BoardNet.THREE_VOLTS_THREE, BoardNet.GROUND, volts=3.3
            )
            check.drive_state(board.sensors["A1"], initial=True)
            check.voltage_at(
                bank,
                expected_pin,
                between=LOGIC_LOW,
                because="A1's intended input must go low when its piece is present",
            )
        with self.assertRaisesRegex(ValueError, "ASSERTION FAILED"):
            board.run("miswired_A1")
