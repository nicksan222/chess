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

    def test_inrush_stays_inside_the_fuse_pulse_rule(self) -> None:
        # Hot plug at PSU +5 %, least path resistance, fastest dVdt: the fuse sees
        # C141's charge plus the ramped rail; I2t over the whole ramp bounds any
        # 8 ms window (Littelfuse Fuseology p3: <= 20 % of nominal melting I2t).
        board = routed_board()
        path = series_path(board, _fuse_mpn(), "low")
        melting = FUSES[_fuse_mpn()][1]
        circuit = self.stage.front_end(
            "Generated chess-board eFuse inrush [BEH]",
            _corner(fast=True, ron="low"),
            f"PULSE(0 {datasheets.PSU_VOLTS.high} 0 1u 1u 1 2)",
            path_ohms=path.total_ohms,
            run_on=True,
        )
        circuit.rows.extend(self._rail_caps())
        circuit.rows.append(".tran 10u 60m uic")
        circuit.controls.extend(
            (
                "let i = -i(vpsu)",
                "let e = integ(i * i)",
                "let result_i2t = e[length(e) - 1]",
                "let result_rail_60ms = v(out)[length(e) - 1]",
            )
        )
        circuit.expect("i2t", 0.0, datasheets.FUSE_PULSE_I2T_FRACTION * melting)
        circuit.expect(
            "rail_60ms", datasheets.SK9822_VDD.low, datasheets.PSU_VOLTS.high
        )
        run_circuit("test_efuse_inrush.py", circuit)

    def test_slowest_ramp_still_reaches_the_rail(self) -> None:
        circuit = self.stage.front_end(
            "Generated chess-board eFuse slow start [BEH]",
            _corner(fast=False),
            f"PULSE(0 {datasheets.PSU_VOLTS.low} 0 1u 1u 1 2)",
            path_ohms=0.0,
            run_on=True,
        )
        circuit.rows.extend(self._rail_caps())
        circuit.rows.append(".tran 100u 120m uic")
        circuit.controls.append("meas tran result_rail FIND v(out) AT=110m")
        circuit.expect("rail", datasheets.SK9822_VDD.low, datasheets.PSU_VOLTS.low)
        run_circuit("test_efuse_slow_start.py", circuit)

    def _op(
        self,
        name: str,
        supply: float,
        *,
        run_on: bool = True,
        high: bool = True,
        load_ohms: float | None = None,
        ilim_high: bool = True,
    ) -> SpiceCircuit:
        """Operating point at one OVLO trip corner (`high`: latest trip)."""
        corner = _corner(fast=True, ilim_high=ilim_high)
        if not high:
            corner = Corner(
                corner.ron,
                datasheets.EFUSE_THRESHOLD_RISING_VOLTS.low,
                corner.slew_volts_per_s,
                corner.ilim,
            )
        circuit = self.stage.front_end(
            name,
            corner,
            str(supply),
            path_ohms=self.path_ohms,
            run_on=run_on,
            static=True,
            trip="high" if high else "low",
        )
        circuit.rows.append(
            f"RLOAD out 0 {load_ohms if load_ohms is not None else '1k'}"
        )
        circuit.rows.append(".op")
        return circuit

    def test_ovlo_window_sits_between_the_supply_and_a_wrong_adapter(self) -> None:
        # User decision (2026-10-06): every in-spec supply turns on (GST25B05 +5 %
        # plus half its 80 mVp-p ripple) and 6.0 V is cut off, at every corner.
        stage = self.stage
        latest, earliest = stage.ovlo_trip(high=True), stage.ovlo_trip(high=False)
        supply_peak = datasheets.PSU_VOLTS.high + datasheets.PSU_RIPPLE_VOLTS_PP / 2
        self.assertGreaterEqual(earliest, 5.30)
        # SK9822-A: the in-spec supply stays within the LEDs' recommended 5.3 V;
        # the trip window above it is ASSUMPTION "LED supply window".
        self.assertLessEqual(
            datasheets.PSU_VOLTS.high, datasheets.SK9822_VDD_RECOMMENDED_MAX
        )
        self.assertGreater(earliest, supply_peak)
        self.assertLess(latest, 6.0)
        for name, supply, on in (
            ("supply_peak", supply_peak, True),
            ("wrong_6v", 6.0, False),
        ):
            circuit = self._op(
                f"Generated chess-board OVLO {name} [BEH]", supply, high=not on
            )
            circuit.controls.append("let result_rail = v(out)")
            if on:
                circuit.expect("rail", 4.9, supply)
            else:
                circuit.expect("rail", -0.01, 0.01)
            with self.subTest(case=name):
                run_circuit(f"test_efuse_ovlo_{name}.py", circuit)

    def test_over_voltage_supplies_are_cut_off(self) -> None:
        ovp = datasheets.PSU_RATED_VOLTS * datasheets.PSU_OVER_VOLTAGE_FRACTION.high
        stage = self.stage
        for supply in (6.0, ovp, 12.0):
            circuit = self._op(
                f"Generated chess-board {supply:g} V supply [BEH]", supply
            )
            circuit.controls.extend(
                (
                    "let result_rail = v(out)",
                    "let result_input_ma = abs(i(vpsu)) * 1000",
                )
            )
            circuit.expect("rail", -0.01, 0.01)
            # Below SMBJ12CA VBR (13.3 V) the TVS is off: only the dividers and
            # the rocker's wetting load draw current, up to a 12 V wrong adapter
            # (user decision D2).
            bias = supply * sum(
                1 / sum(stage.ohms(role, -1) for role in roles)
                for roles in (
                    ("wetting",),
                    ("ovlo_top", "ovlo_bottom"),
                    ("enable_top", "enable_bottom"),
                )
            )
            self.assertLess(supply, datasheets.TVS_BREAKDOWN_VOLTS.low)
            circuit.expect("input_ma", 0.0, 1000 * bias * 1.01)
            with self.subTest(supply=supply):
                run_circuit(f"test_efuse_supply_{supply:g}.py", circuit)

    def _plug(
        self,
        name: str,
        supply: str,
        *,
        high: bool,
        ovlo_filter: bool = True,
        henries: float = 0.0,
        end_ms: float = 30.0,
        load_ohms: float = 1e3,
    ) -> SpiceCircuit:
        """Plug-in through the cord (L in series with the low-corner path R) with
        the rocker on, at the fastest dVdt; `high` picks the latest OVLO trip."""
        rising = datasheets.EFUSE_THRESHOLD_RISING_VOLTS
        base = _corner(fast=True, ron="low")
        corner = Corner(
            base.ron,
            rising.high if high else rising.low,
            base.slew_volts_per_s,
            base.ilim,
        )
        circuit = self.stage.front_end(
            name,
            corner,
            supply,
            path_ohms=self.path_ohms,
            run_on=True,
            trip="high" if high else "low",
            ovlo_filter=ovlo_filter,
            path_henries=henries,
        )
        circuit.rows.extend(self._rail_caps())
        circuit.rows.append(f"RLOAD out 0 {load_ohms}")
        circuit.rows.append(f".tran 10u {end_ms}m 0 10u uic")
        return circuit

    def test_hot_plug_ring_needs_the_ovlo_filter(self) -> None:
        # The cord's inductance rings into C141 at plug-in (up to about 9-10 V,
        # below D1's 13.3 V). At the earliest-trip corner (low divider, VOV(R)
        # and VOV(F) low, leakage in, smallest C) the ring trips OVLO and its last
        # troughs stay above the restart level, so without C144 a +5 % supply never
        # turns on; with C144 the pin never reaches VOV(R) and the board starts.
        supply = datasheets.PSU_VOLTS.high + datasheets.PSU_RIPPLE_VOLTS_PP / 2
        self.assertGreater(supply, self.stage.ovlo_release(high=False))
        for henries in datasheets.PSU_CORD_HENRIES:
            for ovlo_filter in (False, True):
                circuit = self._plug(
                    f"Generated chess-board hot plug, filter {ovlo_filter} [BEH]",
                    f"PULSE(0 {supply} 0 1u 1u 1 2)",
                    high=False,
                    ovlo_filter=ovlo_filter,
                    henries=henries,
                )
                circuit.controls.extend(
                    (
                        "meas tran result_dc_fused_peak MAX v(in)",
                        "meas tran result_rail FIND v(out) AT=29m",
                    )
                )
                circuit.expect("dc_fused_peak", supply * 1.1, 20.0)
                if ovlo_filter:
                    circuit.expect("rail", datasheets.SK9822_VDD.low, supply)
                else:
                    circuit.expect("rail", -0.01, 0.05)
                label = f"{henries * 1e6:g}uH_{'c144' if ovlo_filter else 'bare'}"
                with self.subTest(henries=henries, ovlo_filter=ovlo_filter):
                    run_circuit(f"test_efuse_hot_plug_{label}.py", circuit)

    def test_wrong_adapter_trips_before_the_rail_rises(self) -> None:
        # A 12 V adapter, slowest trip corner (high divider, largest C144): OVLO
        # must trip while the dVdt-ramped output is still far below the LEDs.
        circuit = self._plug(
            "Generated chess-board 12 V plug [BEH]",
            "PULSE(0 12 0 1u 1u 1 2)",
            high=True,
            henries=max(datasheets.PSU_CORD_HENRIES),
            end_ms=10.0,
        )
        circuit.controls.extend(
            (
                "meas tran trip WHEN v(xu74.ov)=0.5 RISE=1",
                "let result_trip_ms = trip * 1000",
                "print result_trip_ms",
                "meas tran result_rail_peak MAX v(out)",
            )
        )
        circuit.expect("trip_ms", 0.0, 2.0)
        circuit.expect("rail_peak", 0.0, 0.5)
        run_circuit("test_efuse_wrong_adapter.py", circuit)

    @residual("OVLO filter")
    def test_running_supply_step_reaches_the_rail_until_ovlo_trips(self) -> None:
        # Residual of C144 (ASSUMPTION "OVLO filter"): with the output on, a supply
        # stepping from 5 V to 6 V or the GST over-voltage maximum (7 V, below
        # D1's 13.3 V) reaches the rail until the filtered OVLO trips: the bulk
        # capacitors' charging current fast-trips U74, which then charges them at
        # ILIM (SLVSFC9C 7.3.5.4); they then hold the rail until the load drains it.
        # Slowest trip corner; minimum load = the 64 LEDs' static current.
        leds = board_circuits().components
        led_count = sum(c.GetFieldText("PartKey") == "SK9822" for c in leds.values())
        idle_ohms = datasheets.PSU_RATED_VOLTS / (
            led_count * datasheets.SK9822_STATIC_AMPS
        )
        rated = datasheets.PSU_RATED_VOLTS
        ovp = rated * datasheets.PSU_OVER_VOLTAGE_FRACTION.high
        for step in (6.0, ovp):
            circuit = self._plug(
                f"Generated chess-board running step to {step:g} V [BEH]",
                f"PWL(0 0 1u {rated} 40m {rated} 40.001m {step})",
                high=True,
                end_ms=100.0,
                load_ohms=idle_ohms,
            )
            circuit.controls.extend(
                (
                    "meas tran result_rail_before FIND v(out) AT=39m",
                    "meas tran trip WHEN v(xu74.ov)=0.5 RISE=1",
                    "let result_trip_ms = (trip - 40m) * 1000",
                    "meas tran result_rail_peak MAX v(out) FROM=40m TO=100m",
                    "meas tran over_start WHEN v(out)=5.5 RISE=1",
                    "meas tran over_end WHEN v(out)=5.5 FALL=1",
                    "let result_over_ms = (over_end - over_start) * 1000",
                    "print result_trip_ms result_over_ms",
                )
            )
            circuit.expect("rail_before", 4.9, rated)
            circuit.expect("trip_ms", 0.0, RUNNING_STEP_TRIP_MS)
            circuit.expect("rail_peak", 5.5, RUNNING_STEP_PEAK_VOLTS)
            circuit.expect("over_ms", 0.0, RUNNING_STEP_OVER_MS)
            with self.subTest(step=step):
                run_circuit(f"test_efuse_running_step_{step:g}.py", circuit)

    @residual("OVLO window")
    def test_ovlo_restart_is_a_latch_off_at_normal_supplies(self) -> None:
        # Reviewer m1: after a trip U74 restarts only below VOV(F) x divider
        # (4.854-5.173 V). A supply back at +5 % never restarts (unplug and replug);
        # back at a nominal 5.0 V it restarts only at the highest-release corner.
        stage = self.stage
        self.assertGreater(datasheets.PSU_VOLTS.high, stage.ovlo_release(high=True))
        self.assertLess(stage.ovlo_release(high=False), datasheets.PSU_RATED_VOLTS)
        self.assertGreater(stage.ovlo_release(high=True), datasheets.PSU_RATED_VOLTS)
        rated = datasheets.PSU_RATED_VOLTS
        for back, high, latched in (
            (datasheets.PSU_VOLTS.high, True, True),
            (datasheets.PSU_VOLTS.high, False, True),
            (rated, False, True),
            (rated, True, False),
        ):
            circuit = self._plug(
                f"Generated chess-board OVLO return to {back:g} V [BEH]",
                f"PWL(0 0 1u {rated} 40m {rated} 40.001m 6.0 50m 6.0 50.001m {back})",
                high=high,
                end_ms=90.0,
            )
            circuit.controls.append(
                "meas tran result_ovlo_state FIND v(xu74.ov) AT=89m"
            )
            if latched:
                circuit.expect("ovlo_state", 0.9, 1.1)
            else:
                circuit.expect("ovlo_state", -0.1, 0.1)
            corner = "late" if high else "early"
            with self.subTest(back=back, corner=corner):
                run_circuit(f"test_efuse_ovlo_return_{back:g}_{corner}.py", circuit)

    def test_reversed_plug_is_blocked(self) -> None:
        circuit = self._op(
            "Generated chess-board reversed plug [BEH]", -datasheets.PSU_VOLTS.high
        )
        limit = datasheets.EFUSE_REVERSE_PIN_AMPS_MAX
        stage = self.stage
        top, bottom = stage.ohms("ovlo_top"), stage.ohms("ovlo_bottom")
        en_top, en_bottom = stage.ohms("enable_top"), stage.ohms("enable_bottom")
        # Pin (clamp) current = current in the top resistor minus the bottom's.
        circuit.controls.extend(
            (
                "let result_rail = v(out)",
                f"let result_ovlo_pin = abs((v(in) - v(ovlo)) / {top} - v(ovlo) / {bottom})",
                f"let result_en_pin = abs((v(run) - v(en)) / {en_top} - v(en) / {en_bottom})",
            )
        )
        circuit.expect("rail", -0.01, 0.01)
        circuit.expect("ovlo_pin", 0.0, limit)
        circuit.expect("en_pin", 0.0, limit)
        run_circuit("test_efuse_reversed.py", circuit)

    @residual("Reversed 12 V adapter")
    def test_reversed_wrong_adapter_exceeds_the_bias_pin_limit(self) -> None:
        # User decision D2: a reversed 12 V adapter keeps the rail off (IN within
        # its -15 V rating, D1 off below 13.3 V) but drives about 12 V / 604k into
        # the EN and OVLO pins, above TI's 10 uA (SLVSFC9C 8.2): recorded in
        # ASSUMPTION "Reversed 12 V adapter"; the bound here is that residual.
        circuit = self._op("Generated chess-board reversed 12 V [BEH]", -12.0)
        stage = self.stage
        top = stage.ohms("ovlo_top", -1)
        self.assertGreater(-12.0, datasheets.EFUSE_IN_MIN_VOLTS)
        self.assertGreater(12.0 / top, datasheets.EFUSE_REVERSE_PIN_AMPS_MAX)
        circuit.controls.extend(
            (
                "let result_rail = v(out)",
                f"let result_ovlo_pin = abs((v(in) - v(ovlo)) / {top})",
            )
        )
        circuit.expect("rail", -0.01, 0.01)
        circuit.expect("ovlo_pin", 0.0, 1.05 * 12.0 / top)
        run_circuit("test_efuse_reversed_12v.py", circuit)

    def test_rocker_off_removes_the_rail(self) -> None:
        circuit = self._op(
            "Generated chess-board rocker off [BEH]",
            datasheets.PSU_VOLTS.high,
            run_on=False,
        )
        circuit.controls.append("let result_rail = v(out)")
        circuit.expect("rail", -0.01, 0.01)
        run_circuit("test_efuse_rocker_off.py", circuit)

    def test_approved_cap_runs_and_full_white_overloads_the_efuse(self) -> None:
        # ILIM (RILM 1.65 kOhm) 1.80-2.20 A: full white must exceed its maximum and
        # the approved cap must stay under its minimum, which the operating point
        # checks. What full white then does (fast trip into limiting, or the
        # ITIMER breaker) is the transient in test_led_switch (S6d).
        board = board_circuits()
        white = board.power_current(full_white=True)
        approved = board.power_current()
        ilim = datasheets.EFUSE_ILIM_AMPS_AT_1K65
        self.assertGreater(white, ilim.high)
        self.assertLess(approved, ilim.low)
        nominal = datasheets.PSU_RATED_VOLTS
        circuit = self._op(
            "Generated chess-board approved load [BEH]",
            nominal,
            load_ohms=nominal / approved,
            ilim_high=False,
        )
        circuit.controls.extend(
            ("let result_rail = v(out)", "let result_input = -i(vpsu)")
        )
        circuit.expect("rail", datasheets.SK9822_VDD.low, nominal)
        circuit.expect("input", 0.0, ilim.low)
        run_circuit("test_efuse_approved.py", circuit)

    def test_full_white_exceeds_the_supply_overload_and_the_fuse(self) -> None:
        # Budget, not a sag model: a 2 A supply hiccups (110-150 % overload) and
        # the fuse is rated 2 A, so full white must be refused by firmware.
        amps = board_circuits().power_current(full_white=True)
        overload = datasheets.PSU_RATED_AMPS * datasheets.PSU_OVERLOAD_FRACTION.high
        self.assertGreater(amps, overload)
        self.assertGreater(amps, datasheets.PSU_RATED_AMPS)


    def test_rail_settles_after_switch_on_with_every_fitted_capacitor(self) -> None:
        circuit = board_circuits().power_startup().clear_expectations()
        circuit.expect("5v_at_1ms", *BOARD_POWER.healthy_rail.tuple())
        run_circuit("test_power_startup.py", circuit)
