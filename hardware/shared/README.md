# Shared hardware definitions

This directory is the tool-independent contract between hardware domains.

- `dimensions/` separates shared measurements by physical object: `board.py`,
  `case.py`, `panel.py`, and `tile_plate.py`. `printing.py` owns process limits;
  `validation.py` checks fit across those objects. PCB routing rules and CAD
  presentation settings remain in their own domains.
- `components/<part>.py` owns each approved product: manufacturer, exact MPN,
  package, body metadata, and datasheet link. The package registry enumerates them.
- `electronics/` owns tool-independent component families and typed pin semantics.
- `panel_buttons.py` owns each control button's position, typed header pin,
  switch reference, and routing priority.
- `hall_banks.py` owns compact bank membership, P-port order, labels, and address
  straps; dimensions and wiring consume it.
- `wiring.py` owns net names, host GPIO assignments, square-to-sensor mapping,
  and LED chain order.

Shared code must never import Blender, Schemdraw, Gerbonara, or KiCad. Domain
folders compose these definitions and own only rendering/tool behavior.

Shared Python is linted and format-checked with Ruff and strictly type-checked
with Basedpyright. Both explicit and inferred dynamic types are rejected. Run
`just --justfile hardware/shared/justfile check`; the root
`just precommit` and `just check` recipes compose it with the other packages.
