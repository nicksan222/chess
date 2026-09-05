# Prototype evidence

These are human measurements, not generated data. D-PROTOTYPE fabrication is
blocked until `hall-magnet.json` passes the production release gate
`build.physical_evidence()`.

Measure the DRV5032FCDBZR with both magnet poles at the final assembled spacing.
The record must contain schema `1`, board revision `D-PROTOTYPE`, sensor MPN,
`pass: true`, positive `final_gap_mm`, nonempty notes, and `north`/`south` objects.
Each pole needs at least five positive `operate_mm` and `release_mm` samples.
Every operate sample must exceed final gap by at least 0.5 mm.

Do not create a passing record without taking the measurements. That function is the
executable schema; `review` does not assert physical release readiness.
