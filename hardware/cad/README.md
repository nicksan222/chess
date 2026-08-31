# Mechanical design

Blender is the source of truth for printable parts. Every project is generated
from Python; derived manufacturing files are not source models.

Revision B is **two printed parts**: a case that holds one PCB, the Raspberry Pi
and the control panel, and a single tile plate that lays the checkerboard over
the whole playing area. Revision A needed 129 prints to cover a board — 64 tile
lids, 64 trays and a tray — and all of that is gone.

Both parts are larger than a desktop printer bed, so they are quoted from an FDM
print service. `REFERENCE_DESKTOP_BUILD_VOLUME_MM` exists to state that fact
rather than to gate anything.

Regenerate everything from the repository root with:

```sh
./tools/cad
```

## Layout

This directory has the same shape as `hardware/pcb`: generated output
in `generated/`, everything that produces it in a subdirectory.

```
generated/    .blend models and PNG renders, one set per project
core/         dimensions, modeling, materials, presentation, validation
blocks/       reusable groups of geometry
projects/     one directory per model, each with generate.py
tests/
references/   inspiration and measurement references, not source
```

Never edit anything in `generated/`; rerun the build instead.

## Adding a project

Add a directory under `projects/` with a `generate.py` that defines `build()`.
The runner discovers it. A project may include a `generation-order` file
containing a non-negative integer when it depends on another project's output;
projects without one default to 100. Lower numbers run first.

A generator writes `GENERATED / f"{NAME}.blend"` plus one PNG per view, named
`<project>.png` or `<project>-<view>.png`.

## Shared modules

`../shared/dimensions.py` is the authoritative source for measurements shared across
projects. It derives the playing span from square size and grid count, derives
the plate span from fit clearance, and validates the vertical stack, the control
panel layout, the board support positions and the plate fixings. Project READMEs
describe intent rather than duplicating those values. Dimension tests run the
same validation without Blender; `./tools/cad` then generates with it.

Coordinates are centred on the **playing area**, not the case. The control strip
extends in negative Y, so the case carries `CASE_CENTER_OFFSET_Y_MM` while square
centres, LED positions and reed positions stay symmetric about the origin.

Both printable parts are generated in **assembly coordinates**: the case floor at
z = 0 and the plate occupying the top 3 mm. `board-assembly` therefore moves
neither of them, so a gap between case and plate is a real dimension error rather
than a positioning mistake in a view.

`core/materials.py` owns procedural presentation materials. They make review
renders readable but do not specify purchased material, finish, or process.

`core/validation.py` checks generated meshes for positive volume, manifold
edges, millimetre-scale bounding boxes, and fit inside their reference build
volumes.

`core/modeling.py` and `core/presentation.py` hold shared mesh operations,
studio setup and library loading. `blocks/pcb_proxy.py` builds a presentation
stand-in for the populated circuit board; `hardware/pcb` owns the real
design.

Every printable model has one owning generator. `board-assembly` imports those
exact generated objects rather than redefining printable geometry.

### Two boolean traps worth knowing

Both cost real debugging time, and both fail silently rather than reporting an
error, so `core/modeling.py` guards against them:

- **A bevel radius must be under half the box's thinnest dimension.** Wider than
  that, the bevel folds through itself and Blender produces an invalid mesh
  without complaining. `rounded_box` now refuses it outright. The studio floor
  had been quietly invalid for exactly this reason.
- **Cutters batched into one operand must be disjoint.** `cut_batch` joins
  meshes, which is concatenation and not a union, so overlapping members give the
  exact solver a self-intersecting operand and it deletes the body entirely.
  Crossing grid grooves, and a screw shaft with its own head recess, therefore go
  in separate batches.

## Toolchain

`./tools/cad` downloads a checksum-verified Blender build into the ignored
`.cache` directory if one is not already there. Set `BLENDER_BIN` to use an
existing install instead, which is required on platforms without a published
Linux x86_64 build. Manufacturing exports remain deliberately separate.
