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
