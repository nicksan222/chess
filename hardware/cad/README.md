# Mechanical design

Blender is the source of truth for printable parts. Every project is generated
from Python; derived manufacturing files are not source models.

Regenerate everything from the repository root with:

```sh
./tools/cad
```

## Layout

This directory has the same shape as `hardware/electronics`: generated output
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

`core/dimensions.py` is the authoritative source for measurements shared across
projects. It derives the playing span from square size and grid count, derives
the physical tile size from fit clearance, and validates the printable
enclosure, Velcro pockets, optional screw mounts, and board envelope. Project
READMEs describe intent rather than duplicating those values. Dimension tests
run the same validation without Blender; `./tools/cad` then generates with it.

`core/materials.py` owns procedural presentation materials. They make review
renders readable but do not specify purchased material, finish, or process.

`core/validation.py` checks generated meshes for positive volume, manifold
edges, millimetre-scale bounding boxes, and fit inside their reference build
volumes.

`core/modeling.py` and `core/presentation.py` hold shared mesh operations,
studio setup and library loading. `blocks/tile_electronics.py` builds the wired
single-tile reference.

Every printable model has one owning generator. The universal tile lid and tray
are separate projects; `single-tile-merged` and `board-assembly` import those
exact generated objects rather than redefining printable geometry.

## Toolchain

`./tools/cad` downloads a checksum-verified Blender build into the ignored
`.cache` directory if one is not already there. Set `BLENDER_BIN` to use an
existing install instead, which is required on platforms without a published
Linux x86_64 build. Manufacturing exports remain deliberately separate.
