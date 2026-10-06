"""Behavioural [BEH] TPS259474A eFuse circuits built from the board and its datasheet.

No vendor model is used: the eFuse is a datasheet-table behaviour (TI SLVSFC9C).
It conducts IN -> OUT through RON only while EN/UVLO is above its rising threshold,
the OVLO comparator is released and IN is above its fixed UVP (2.53 V); it never
conducts OUT -> IN (back-to-back FETs); its output follows a dVdt ramp of
SR = 0.905 x IdVdt / CdVdt (fitted to CdVdt(pF) = 2000 / SR(V/ms) at the typical
2.21 uA). OVLO has the datasheet hysteresis (§7.3.3): it trips above VOV(R) within
tOVLO (1.2 us) and releases only below VOV(F); after a release the output ramps
again from 0 (474A: dVdt restart). EN and OVLO thresholds are separate corners.

Overcurrent is the TPS259474A's (S6d, hardware-engineer-breaker.md):
- start-up (from turn-on until the ramp and OUT reach IN): active limit at ILIM,
  no timer (§7.3.5.3 note 3);
- steady state: no limiting; above ILIM the board's ITIMER capacitor discharges
  at IITIMER and after dVITIMER the breaker opens (§7.3.5.2), stays off tRST and
  restarts with dVdt (§6.6, 474A auto-retry);
- above ISC = 2.01 x ILIM: fast trip, then back on limiting at ILIM until the load
  wants less than ILIM (§7.3.5.4).
Not modelled: thermal shutdown (no transient thermal impedance is published), the
30 us fast-trip de-glitch and the foldback below VFB. Which overload branch a
part takes depends on its ISC, published as typical only (and tSC only above
3 x ILIM), so tests bound both branches. The `static` (operating point) form has
no states and is valid only under ILIM (`_static_rows`).
The divider, filter, timer, wetting and timing values come from the parts placed
on the board (`BoardHarness.power_topology`).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from shared.electronics import ComponentReference, EfusePin
from spice import datasheets
from spice.board_harness import BoardHarness
from spice.circuit import SpiceCircuit
from spice.datasheets import Span

UVP_VOLTS = 2.53  # SLVSFC9C 6.5 VUVP(R) typ: below this the device stays off.
EDGE = 0.002  # Smoothing width of the behavioural comparators (V).
DVDT_GAIN = (
    datasheets.EFUSE_DVDT_PF_VOLTS_PER_MS
    * 1e-12
    * 1e3
    / datasheets.EFUSE_DVDT_TYPICAL_AMPS
)
DVDT_FARADS = 10e-9  # C142 (CAP_10N) on DVDT.
# Generic clamp for a pin's ESD diode to GND in a reversed plug [BEH].
PIN_CLAMP_MODEL = ".model PINCLAMP D(IS=1e-14 N=1)"
STATE_EDGE = 0.01  # Smoothing width of the state latches (0..1).
# Ceramic capacitors the model can read from the board, by part key.
CAPACITOR_FARADS = {"CAP_1N": 1e-9, "CAP_10N": 10e-9}
TimerCorner = Literal["slow", "fast"]


@dataclass(frozen=True)
class Timer:
    """ITIMER blanking: the board's capacitor, discharge current and threshold."""

    farads: float
    amps: float
    delta_volts: float

    @property
    def blanking_s(self) -> float:
        """Time above ILIM before the breaker opens (SLVSFC9C eq. 6)."""
        return self.farads * self.delta_volts / self.amps


@dataclass(frozen=True)
class Corner:
    """One datasheet corner: RON, OVLO rising/falling and EN rising thresholds."""

    ron: float
    threshold: float
    slew_volts_per_s: float
    ilim: float
    release: float | None = None
    enable: float | None = None

    @property
    def ovlo_release(self) -> float:
        """VOV(F) at the same end of its range as the rising threshold."""
        if self.release is not None:
            return self.release
        rising, falling = (
            datasheets.EFUSE_THRESHOLD_RISING_VOLTS,
            datasheets.EFUSE_THRESHOLD_FALLING_VOLTS,
        )
        return falling.high if self.threshold >= rising.high else falling.low

    @property
    def enable_threshold(self) -> float:
        """EN rising threshold; falls back to the OVLO threshold when no separate EN corner is set."""
        return self.threshold if self.enable is None else self.enable


def _soft(expr: str, width: float) -> str:
    """Smooth 0->1 step of an expression around 0."""
    return f"0.5 * (1 + tanh(({expr}) / {width}))"


def _step(node: str, threshold: float) -> str:
    """Smooth 0->1 comparator: a tanh step 2 mV wide (far inside the datasheet
    threshold spread) so Newton iterations converge."""
    return f"0.5 * (1 + tanh((V({node},gnd) - {threshold}) / {EDGE}))"


def _latch(name: str, set_expr: str, hold_expr: str) -> list[str]:
    """A 0/1 state node `name`: set by `set_expr`, kept while `hold_expr` (1 us)."""
    return [
        f"B{name} {name}s gnd V={{max({set_expr}, {hold_expr})}}",
        f"R{name} {name}s {name} 1k",
        f"C{name} {name} gnd 1n",
    ]


def _on(state: str) -> str:
    """A latch read as a sharp 0/1, so a partly set state never leaks."""
    return f"0.5 * (1 + tanh((V({state},gnd) - 0.5) / {STATE_EDGE}))"


def _static_rows(name: str, corner: Corner) -> list[str]:
    """Operating point: no ramp, no OVLO memory, OUT follows IN through RON.

    A static approximation for loads under ILIM only (approved load, OVLO and
    reversed-plug operating points): it saturates at ILIM like an active limit,
    which the TPS259474A is not in steady state (reviewer-s6d m3). `front_end`
    asserts the input current stays under ILIM min, so an overload operating
    point fails instead of silently using it; overloads are transients.
    """
    ron = max(corner.ron, 1e-4)
    return [
        f".subckt {name} in out en ovlo gnd",
        f"Bov ov gnd V={{{_step('ovlo', corner.threshold)}}}",
        (
            f"Bon on gnd V={{{_step('en', corner.enable_threshold)}"
            f" * {_step('in', UVP_VOLTS)} * (1 - V(ov,gnd))}}"
        ),
        "Vramp ramp gnd 1e3",
        (
            f"Bpass in out I={{V(on,gnd) * {corner.ilim} * tanh(max(0, "
            f"min(V(in,gnd), V(ramp,gnd)) - V(out,gnd)) / ({corner.ilim} * {ron}))}}"
        ),
        ".ends",
    ]


def efuse_rows(
    name: str, corner: Corner, *, static: bool = False, timer: Timer | None = None
) -> list[str]:
    """Subcircuit IN OUT EN OVLO GND for one datasheet corner.

    `static` (operating point): see `_static_rows`. Otherwise a 1 F integrator
    ramps at the corner's slew rate; `ov` holds the OVLO state with hysteresis;
    `sd` marks start-up done; `fl` the post-fast-trip limit; `td` the ITIMER
    discharge (volts) on `timer`; `cb` the open breaker, released by `rt` after
    tRST. `timer` is required for a transient.
    """
    if static:
        return _static_rows(name, corner)
    if timer is None:
        raise ValueError("a transient eFuse needs the board's ITIMER")
    ron = max(corner.ron, 1e-4)
    ilim = corner.ilim
    isc = datasheets.EFUSE_ISC_RATIO * ilim
    done, limiting, broken = _on("sd"), _on("fl"), _on("cb")
    drop = "max(0, min(V(in,gnd), V(ramp,gnd)) - V(out,gnd))"
    limit_mode = f"max(1 - {done}, {limiting})"
    ceiling = f"({ilim} * {limit_mode} + {4 * isc} * (1 - {limit_mode}))"
    current = f"(V(on,gnd) * {ceiling} * tanh({drop} / ({ceiling} * {ron})))"
    unlimited = f"(V(on,gnd) * {4 * isc} * tanh({drop} / ({4 * isc * ron})))"
    over = _soft(f"{current} - {ilim}", 0.01)
    demand = _soft(f"{drop} / {ron} - {ilim}", 0.01)
    started = (
        f"{_soft('V(ramp,gnd) - V(in,gnd)', 0.01)}"
        f" * {_soft('V(out,gnd) - V(in,gnd) + 0.2', 0.01)}"
    )
    trip, release = _step("ovlo", corner.threshold), _step("ovlo", corner.ovlo_release)
    return [
        f".subckt {name} in out en ovlo gnd",
        f"Bset ovs gnd V={{max({trip}, min({release}, V(ov,gnd)))}}",
        "Rov ovs ov 1k",
        "Cov ov gnd 1n",
        *_latch(
            "cb",
            _soft(f"V(td,gnd) - {timer.delta_volts}", 0.002),
            f"min({broken}, 1 - {_soft('V(rt,gnd) - 1', 0.005)})",
        ),
        "Crt rt gnd 1",
        (
            f"Brt gnd rt I={{{broken} / {datasheets.EFUSE_RETRY_S}"
            f" - {_soft('0.1 - V(cb,gnd)', 0.01)} * V(rt,gnd) * 1e4}}"
        ),
        (
            f"Bon on gnd V={{{_step('en', corner.enable_threshold)}"
            f" * {_step('in', UVP_VOLTS)} * (1 - V(ov,gnd)) * (1 - {broken})}}"
        ),
        "Cramp ramp gnd 1",
        (
            f"Bramp gnd ramp I={{V(on,gnd) * {corner.slew_volts_per_s}"
            f" * {_soft('V(in,gnd) + 1 - V(ramp,gnd)', 0.05)}}}"
        ),
        # Off (OVLO, EN, UVP or breaker): the ramp restarts from 0 (474A).
        f"Breset ramp gnd I={{{_soft('0.5 - V(on,gnd)', 0.01)} * V(ramp,gnd) * 1e4}}",
        "Rramp ramp gnd 1e12",
        *_latch(
            "sd",
            f"{started} * {_soft('V(on,gnd) - 0.5', 0.01)}",
            f"{done} * {_soft('V(on,gnd) - 0.5', 0.01)}",
        ),
        *_latch(
            "fl",
            f"{_soft(f'{unlimited} - {isc}', 0.01)} * {done} * V(on,gnd)",
            f"min({limiting}, {demand}) * V(on,gnd)",
        ),
        f"Ctd td gnd {timer.farads}",
        (
            f"Btd gnd td I={{{timer.amps} * {over} * {done} * (1 - {limiting})"
            f" * (1 - {broken}) - (1 - {over}) * V(td,gnd)"
            f" / {datasheets.EFUSE_ITIMER_PULLUP_OHMS} - {broken} * V(td,gnd) * 1e-3}}"
        ),
        f"Bpass in out I={{{current}}}",
        ".ends",
    ]


def tvs_rows(breakdown: float) -> list[str]:
    """Bidirectional SMBJ12CA: a breakdown branch each way at the datasheet IT."""
    return [
        f".model TVSBR D(IS=1e-20 BV={breakdown} IBV={datasheets.TVS_TEST_AMPS} RS=0.07)",
        ".subckt TVS a b",
        "D1 a x TVSBR",
        "D2 b x TVSBR",
        ".ends",
    ]


TripCorner = Literal["low", "high"]


class EfuseBoard:
    """Circuits for the U74 input stage with the board's own bias values."""

    def __init__(self, board: BoardHarness) -> None:
        self.board = board
        self.roles = board.power_topology()

    def ohms(self, role: str, sign: int = 0) -> float:
        """Resistance of the placed resistor for `role`, nominal scaled by its tolerance
        in direction `sign` (-1 low, 0 nominal, +1 high).
        """
        nominal, tolerance = self.board.resistor_ohms(self.roles[role])
        return nominal * (1 + sign * tolerance)

    def ovlo_farads(self, sign: int = 0) -> float | None:
        """The OVLO filter capacitor on the board (C144, S4c), with X7R tolerance."""
        ovlo = self.roles["ovlo"]
        for reference, component in self.board.components.items():
            nets = {self.board.net_by_endpoint.get((reference, pin)) for pin in "12"}
            if component.GetFieldText("PartKey") == "CAP_10N" and nets == {ovlo, "GND"}:
                return 10e-9 * (1 + sign * datasheets.MLCC_X7R_TOLERANCE)
        return None

    def timer(self, corner: TimerCorner) -> Timer:
        """ITIMER from the capacitor the board places on U74's ITIMER pin.

        `slow`: largest capacitor (X7R +10 %), smallest IITIMER and largest
        dVITIMER, the longest blanking; `fast`: the reverse (SLVSFC9C 6.5).
        """
        pin = (ComponentReference.INPUT_EFUSE, str(EfusePin.OVERCURRENT_TIMER))
        net = self.board.net_by_endpoint[pin]
        # Reviewer-s6d m2: exactly one known capacitor, so a parallel part can
        # never be missed (that would understate the blanking, unsafe for F1).
        found = [
            component.GetFieldText("PartKey")
            for reference, component in self.board.components.items()
            if reference != pin[0]
            and net
            in {self.board.net_by_endpoint.get((reference, p)) for p in ("1", "2")}
        ]
        if len(found) != 1 or found[0] not in CAPACITOR_FARADS:
            raise ValueError(f"{net} must carry exactly one known capacitor: {found}")
        slow = corner == "slow"
        tolerance = datasheets.MLCC_X7R_TOLERANCE * (1 if slow else -1)
        amps, volts = datasheets.EFUSE_ITIMER_AMPS, datasheets.EFUSE_ITIMER_DELTA_VOLTS
        return Timer(
            CAPACITOR_FARADS[found[0]] * (1 + tolerance),
            amps.low if slow else amps.high,
            volts.high if slow else volts.low,
        )
