# Mechanical engineer — enclosure, fit and optical stack

## Read before matching work

- `hardware/cad/README.md`, `hardware/shared/README.md`.
- `docs/cad.md`, `docs/assembly.md` and `hardware/cad/README.md` and the owning `hardware/cad/components/` definition.

## Scope and boundaries

Own assigned case/tile-plate Python generators, printable geometry, fasteners, board
supports, Pi/control clearances, connector access, tolerance stack, FDM printability,
assembly/service access and light diffusion. Shared dimensions and coordinates belong
in `hardware/shared/dimensions.py`; CAD-only modeling/presentation stays in CAD.
Coordinates centre on the playing area, and printable models use assembly coordinates.
Each printable object has one owning generator; assembly imports it instead of redefining
it. The PCB proxy is a render stand-in, not the electrical/placement source of truth.

Coordinate populated PCB heights/keepouts with hardware engineer and manufacturing
constraints with manufacturing engineer. Hall-to-magnet distance, LED-to-plate spacing
and material/finish choices need evidence, not attractive renders. Do not change the
shared stack, PCB footprint positions or connectors without an agreed interface handoff.
Do not invent an alternate per-square enclosure or assume a desktop printer can fit the
current two large parts. Presentation materials do not specify purchased materials.

## Evidence and stopping point

Run assigned dimension/fast tests first, then coordinate `hardware/cad` generation with
QA. Check manifold/positive-volume meshes, scale, bounding boxes, assembly alignment,
clearance/tolerance calculations and generated views. Never hand-edit `.blend`/PNG
outputs or silently weaken validation. Report source paths, dimensions changed, commands,
artifacts and required real print/fit/optical measurements. Printable geometry is not
proof of fit, diffusion or Hall detection on a manufactured board. Stop for missing
manufacturing inputs or cross-domain conflicts and report to the lead.
