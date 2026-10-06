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
