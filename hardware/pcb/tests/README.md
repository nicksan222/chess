# PCB tests

Tests are grouped by the capability they protect:

- `model/` validates components, connectivity, design composition, rules, and repeated squares without requiring KiCad.
- `layout/` validates footprints, placement, and the native KiCad adapter.
- `release/` validates architecture boundaries, generated artifacts, firmware pin parity, and manufacturing policy.
- `spice/` defines readable electrical scenarios in Python, writes a same-named `.cir` beside each case, and lets ngspice execute the registered checks.

Run all groups with `just --justfile hardware/pcb/justfile test`.
