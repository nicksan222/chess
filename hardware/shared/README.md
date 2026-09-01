# Shared hardware definitions

This directory is the tool-independent contract between hardware domains.

- `dimensions.py` owns physical dimensions and coordinates genuinely shared by
  PCB and CAD: enclosure padding and clearances, populated-board placement,
  connector access references, and square-subassembly offsets. PCB-only routing
  rules and CAD-only presentation settings stay in their respective domains.
- `components.py` is the approved-parts catalog: manufacturer, exact MPN,
  package, body metadata, and datasheet links, plus the
  `ComponentImplementation` base class for tool-specific representations.
- `wiring.py` owns net names, host GPIO assignments, square-to-sensor mapping,
  and LED chain order.

CAD, schematic, PCB, and future KiCad implementations may inherit from the base
class, but shared code must never import Blender, Schemdraw, Gerbonara, or KiCad.
Domain folders adapt these definitions and own only rendering/tool behavior.

Shared Python is linted and format-checked with Ruff. From the repository root,
`./tools/python` is the check; it also runs from `./tools/check`, the
pre-commit hook, and CI.
