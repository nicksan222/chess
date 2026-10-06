"""Power scenarios at datasheet corners against the native board (S4/S4b).

Supply path and plane drop are modelled from the routed board; the U74 eFuse is a
behavioural [BEH] model of TI SLVSFC9C (`efuse_model.py`). Assertions are margins
against limits from the parts' own datasheets (`datasheets.py`), not re-derived
equalities.
"""

from __future__ import annotations

import unittest

from spice import datasheets
from spice.circuit import SpiceCircuit
from spice.efuse_model import Corner, EfuseBoard, slew
from spice.plane_mesh import PlaneMesh, routed_board
from spice.power_path import FUSES, pick, series_path
from spice.power_path import Corner as PathCorner
from spice.residuals import residual
from spice.support import board_circuits, run_circuit

# Board rule: the +5V/GND planes may lose at most 50 mV between the supply entry
# and any LED (1 % of 5 V); the source path is budgeted by the corner test below.
PLANE_DROP_BUDGET_VOLTS = 0.050
# Residual of the OVLO filter (S4c, ASSUMPTION "OVLO filter"): when a running supply
# steps to 6-7 V, [BEH] at the slowest trip corner gives a trip after 1.72 / 0.65 ms,
# a rail peak of 5.99 / 6.03 V and 10.5 / 10.0 ms above 5.5 V with only the LEDs'
# static load (the bulk capacitors hold the rail after the trip). Bounds about 10 %
# above those values, so a change that worsens the residual fails.
RUNNING_STEP_TRIP_MS = 2.0
RUNNING_STEP_PEAK_VOLTS = 6.1
RUNNING_STEP_OVER_MS = 12.0
SQUARES = [f"{file}{rank}" for file in "abcdefgh" for rank in range(1, 9)]


def _led_amps(brightness: float) -> float:
    """LED chain current (amps) at a global brightness fraction: static current plus three channels at the datasheet maximum."""
    return (
        datasheets.SK9822_STATIC_AMPS
        + 3 * datasheets.SK9822_CHANNEL_AMPS_MAX * brightness
    )


def _fuse_mpn() -> str:
    """MPN of the fitted input fuse (F1), so the fuse limits come from the board."""
    return board_circuits().components["F1"].GetValue()


def _corner(*, fast: bool, ilim_high: bool = True, ron: PathCorner = "high") -> Corner:
    """An eFuse corner: fast or slow dVdt, high or low ILM overcurrent threshold (circuit breaker), and RON at the chosen end of its range."""
    span = datasheets.EFUSE_DVDT_AMPS
    return Corner(
        ron=pick(datasheets.EFUSE_RON_OHMS, ron),
        threshold=datasheets.EFUSE_THRESHOLD_RISING_VOLTS.high,
        slew_volts_per_s=slew(span.high if fast else span.low),
        ilim=pick(datasheets.EFUSE_ILIM_AMPS_AT_1K65, "high" if ilim_high else "low"),
    )


class SupplyCornerSpiceTest(unittest.TestCase):
    """Worst-corner rail level at every LED and at the Pi, from the full series path and plane mesh."""

    def test_worst_corner_rail_stays_in_range_at_every_led_and_the_pi(self) -> None:
        # Low end: PSU -5 %, every resistance at its maximum (end-of-life contacts,
        # 70 C copper, eFuse RON max), approved LED cap. Floor: SK9822 §8 and
        # AHCT125 §5.2 minimum 4.5 V (the Pi's 4.63 V warning is not met here and is
        # a documented ASSUMPTION; the Zero range has no detector). Since S6 the
        # LEDs sit behind Q1 at its hot maximum RDS(on) (SK9822-A §10: 4.5 V).
        board = routed_board()
        brightness = float(board_circuits().led_brightness_max)
        mesh = PlaneMesh(board)
        cases: tuple[tuple[str, PathCorner, float, float | None], ...] = (
            ("low", "high", datasheets.PSU_VOLTS.low, None),
            (
                "high",
                "low",
                datasheets.PSU_VOLTS.high,
                datasheets.SK9822_VDD_MAX,
            ),
        )
        for name, corner, volts, ceiling in cases:
            path = series_path(board, _fuse_mpn(), corner)
            circuit = mesh.circuit(
                f"Generated chess-board supply corner, {name}",
                led_amps=_led_amps(brightness if name == "low" else 0.0),
                host_amps=datasheets.HOST_AND_LOGIC_AMPS if name == "low" else 0.0,
                supply_volts=volts,
                positive_ohms=path.positive_ohms,
                ground_ohms=path.ground_ohms,
                switch_ohms=pick(datasheets.LED_SWITCH_OHMS, corner),
            )
            floor = datasheets.SK9822_VDD.low if name == "low" else 0.0
            top = ceiling if ceiling is not None else volts
            for square in SQUARES:
                circuit.expect(f"vdd_{square}", floor, top)
            circuit.expect("pi_header", floor, top)
            with self.subTest(corner=name):
                run_circuit(f"test_supply_corner_{name}.py", circuit)


class EfuseSpiceTest(unittest.TestCase):
    """[BEH] TPS259474ARPW behaviour from SLVSFC9C tables, on the board's values."""

    stage: EfuseBoard
    path_ohms: float

    @classmethod
    def setUpClass(cls) -> None:
        """Build the eFuse front end and the low-corner series-path resistance once."""
        cls.stage = EfuseBoard(board_circuits())
        cls.path_ohms = series_path(routed_board(), _fuse_mpn(), "low").total_ohms

    def _rail_caps(self) -> list[str]:
        """SPICE rows for every capacitor fitted between +5V and GND (the capacitance the eFuse charges)."""
        rows: list[str] = []
        for reference, component in self.stage.board.components.items():
            key = component.GetFieldText("PartKey")
            nets = {
                self.stage.board.net_by_endpoint.get((reference, pin))
                for pin in ("1", "2")
            }
            if not key.startswith("CAP_") or nets != {"+5V", "GND"}:
                continue
            if key == "CAP_560U":
                # Rubycon ZLJ: +20 % capacitance, ESR at its 0 lower bound.
                rows.append(f"C{reference} out 0 {datasheets.ZLJ_560U_FARADS.high}")
            else:
                value = {"CAP_100N": "100n", "CAP_10U": "10u"}[key]
                rows.append(f"C{reference} out 0 {value}")
        return rows

    def test_full_white_exposes_supply_sag_and_overcurrent(self) -> None:
        board = board_circuits()
        expected_current = board.power_current(full_white=True)
        circuit = board.power(full_white=True).clear_expectations()
        circuit.expect(
            "current",
            expected_current - BOARD_POWER.current_tolerance_amps,
            expected_current + BOARD_POWER.current_tolerance_amps,
        )
        circuit.expect("5v", *BOARD_POWER.overloaded_rail.tuple())
        run_circuit("test_power_full_white.py", circuit)

    def test_open_switch_removes_the_board_rail(self) -> None:
        circuit = board_circuits().power_off().clear_expectations()
        circuit.expect("5v", *BOARD_POWER.off_rail.tuple())
        run_circuit("test_power_off.py", circuit)

    def test_rail_settles_after_switch_on_with_every_fitted_capacitor(self) -> None:
        circuit = board_circuits().power_startup().clear_expectations()
        circuit.expect("5v_at_1ms", *BOARD_POWER.healthy_rail.tuple())
        run_circuit("test_power_startup.py", circuit)
