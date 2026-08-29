# CAD dimension tests

This directory verifies relationships in the shared CAD dimension source without
starting Blender. Tests cover the millimetre unit contract, compact product
scale, build-volume fit, printable feature minimums, fit clearances, enclosure
arithmetic, and component containment.

The limits are prototype regression guardrails. They do not model material
shrinkage, bridging, layer adhesion, supports, or printer calibration. Generated
mesh topology, volume, and measured bounding boxes are checked separately by
`../validation.py` whenever Blender regeneration runs.

Generator-structure tests also check `generation-order` so the lid, tray,
merged tile, empty board, and board assembly run in dependency order. They
ensure every printable object has one owning generator and that view generators
import those outputs instead of recreating geometry.

The repository quality gate discovers these tests automatically through
`make check`.
