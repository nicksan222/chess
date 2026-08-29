# CAD

## Purpose

Record mechanical source conventions and reviewed design decisions.

## Known direction

Python generators under `hardware/cad/projects` are source; the `.blend`
models they produce live in `hardware/cad/generated`. Manufacturing
exports will be derived later.

Each Blender design owns a directory under `hardware/cad/projects` containing
its generator and documentation; the models and renders it produces are written
to `hardware/cad/generated`. Run `./tools/cad` from the repository root to
regenerate all of them locally, or `./tools/electronics` for the drawings.

Shared CAD measurements live in `hardware/cad/core/dimensions.py`. Derived
relationships are checked during generation, including playing span, overall
frame span, tile enclosure height, and the board support stack.

All modeled physical dimensions use millimetres. The shared file also owns the
compact-board product envelope, prototype FDM feature minimums, fit-clearance
range, reference build volumes, and print-bed margin. Generators must consume
those values rather than repeating physical measurements locally. Run the file
directly to print the current scale summary:

```sh
python3 hardware/cad/core/dimensions.py
```

The selected form factor is intentionally a compact electronic chessboard. It
does not claim tournament-size compliance. For context, the FIDE equipment
specification effective March 2026 recommends 50-60 mm squares:
<https://handbook.fide.com/chapter/ChessEquipmentWithoutElectronicComponenets032026>.

The printer envelopes are regression-test references, not required brands. They
correspond to compact and large-format machine classes represented by Prusa's
published MINI+ and XL build volumes:
<https://cdn.help.prusa3d.com/article/faq-frequently-asked-questions_1932>.
An edge margin is reserved before testing whether a part fits.

Each printable model has one owning generator. The tile lid and tray live in
`projects/single-tile-top` and `projects/single-tile-bottom`;
`projects/single-tile-merged` imports those exact generated objects for merged,
open, and wired views. The empty printable board is a separate element, and
`projects/board-assembly` imports the same generated lid and tray for loading
and finished compositions. View generators do not recreate printable geometry.
Generic modeling, presentation and library-loading code is shared from `core/`,
and the wired tile reference from `blocks/`.

Pure Python tests run in CI without Blender. During local regeneration,
`core/validation.py` additionally rejects non-manifold or zero-volume FDM meshes
and checks each generated part's measured bounding box against its build
envelope.
The exterior trim is treated as cut wood stock, not as a printed board-sized
part.

## TODO

Confirm clearances, wall thicknesses, orientation, material shrinkage, and bed
adhesion with calibrated test prints before producing manufacturing exports.
