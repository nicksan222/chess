# Blender sources

Editable `.blend` files belong here and are treated as project source. The
workflow is editable Blender source first and manufacturing exports later.

Each design lives in its own directory with its editable project, generator,
documentation, and inspection renders. Regenerate every Blender design from the
repository root with:

```sh
make regen-all
```

`dimensions.py` is the authoritative source for measurements shared across CAD
projects. It derives the playing span from square size and grid count, derives
the physical tile size from fit clearance, and validates the printable enclosure,
Velcro placement pockets, optional screw mounts, and printable-board envelope.
Project READMEs describe intent rather than duplicating those values. The
repository quality gate executes the same validation without invoking Blender.

`materials.py` owns procedural presentation materials shared by the projects.
They make review renders readable but do not specify purchased material, finish,
or manufacturing process.

`validation.py` checks generated FDM tile and board meshes for positive volume,
manifold edges, millimetre-scale bounding boxes, and fit inside their reference
build volumes. CI runs dimension tests without launching Blender.

Every printable model has one owning `generate.py`. The universal tile lid and
tray are separate element projects under `single-tile/top` and
`single-tile/bottom`. `single-tile/merged` and `board-assembly` import those exact
generated objects without redefining printable geometry. Shared mesh operations,
studio setup, library loading, and wired references live in `modeling.py`,
`presentation.py`, and `tile_electronics.py`.

The local runner discovers project `generate.py` files recursively. A project
may include a `generation-order` file containing a non-negative integer when it
depends on generated output from another project; projects without one default
to order 100. Adding a project never requires editing the runner.
Run `./tools/generate-cad --list` to inspect the discovered execution order
without starting Blender.

The local generator downloads a checksum-verified Blender build into the ignored
`.cache` directory when `BLENDER_BIN` is not supplied. Manufacturing exports
remain deliberately separate.
