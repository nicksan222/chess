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
regenerate all of them locally, or `./tools/pcb` for the drawings.

## Two printed parts

Revision A needed 129 prints to cover a board: 64 tile lids, 64 tile trays and a
tray to hold them. Revision B needs two.

- **`projects/board-case`** produces `Printable_Board_Case`, 340 x 380 x 30 mm.
  It carries the single PCB on 20 bosses, hangs the Raspberry Pi underneath it,
  and presents twelve buttons and a display through a face-up bezel across the
  front.
- **`projects/tile-plate`** produces `Printable_Tile_Plate`, 319.6 mm square and
  3 mm thick, with the checkerboard engraved into it and a diffuser pocket over
  each LED. It drops into a rebate in the case.

`projects/board-assembly` is the only presentation project. It imports both of
those exact generated objects and adds a non-printed proxy for the populated
circuit board from `blocks/pcb_proxy.py`. View generators do not recreate
printable geometry.

The case is deeper than it is wide by exactly the 40 mm control strip. Putting
the buttons and the display on a face-up strip at the front of the same PCB is
what keeps every component on one side of the board and avoids right-angle parts.

## Coordinates and the assembly datum

Coordinates are centred on the **playing area**, not the case, so square centres,
LED positions and reed positions stay symmetric about the origin while the case
carries `CASE_CENTER_OFFSET_Y_MM`.

Both printable parts are generated in **assembly coordinates**: the case floor at
z = 0, the plate occupying the top 3 mm. `board-assembly` therefore moves neither
of them. That is deliberate — if the plate ever stops meeting the case, it is a
real error in `dimensions.py` rather than a positioning mistake in a view, and
the render shows it.

## Shared measurements

Shared CAD measurements live in `hardware/shared/dimensions.py`, which
validates itself on import. Among other things it checks that the internal stack
— floor, Pi cavity, board, gap, plate — sums exactly to the case height, that
every plate screw lands on the case ledge rather than over the PCB, that no
support boss collides with an LED or a reed, and that every control-panel feature
stays on the control strip.

All modeled physical dimensions use millimetres. Generators must consume those
values rather than repeating physical measurements locally. Run the file directly
to print the current scale summary:

```sh
PYTHONPATH=hardware python3 -m shared.dimensions
```

## Scale

The selected form factor is intentionally a compact electronic chessboard. It
does not claim tournament-size compliance. For context, the FIDE equipment
specification effective March 2026 recommends 50-60 mm squares:
<https://handbook.fide.com/chapter/ChessEquipmentWithoutElectronicComponenets032026>.

40 mm squares suit a set whose king base is 32 mm or less, which covers most
ordinary club sets. Measure before buying magnets.

## Printing

Both parts are larger than a desktop printer bed, so they are quoted from an FDM
print service; 380 mm also exceeds typical MJF and resin build volumes.
`REFERENCE_DESKTOP_BUILD_VOLUME_MM` exists to state that rather than to gate
anything, and the tests assert that neither part fits it. An edge margin is
reserved before testing whether a part fits.

The plate's underside is pocketed square by square, leaving ribs on the grid
lines. A 3 mm solid sheet 320 mm across is a lot of material to have quoted and a
warping risk; the pockets remove about a third of it and double as the clearance
over the reed switches.

## Validation

Pure Python tests run in CI without Blender. During local regeneration,
`core/validation.py` additionally rejects non-manifold or zero-volume FDM meshes
and checks each generated part's measured bounding box against its build
envelope.

Two Blender-specific traps are guarded in `core/modeling.py`, because both fail
silently rather than reporting an error:

- A **bevel radius** must be under half the box's thinnest dimension, or the
  bevel folds through itself and produces an invalid mesh. `rounded_box` refuses
  it. The studio floor had been quietly invalid for exactly this reason.
- Cutters batched into **one boolean operand must be disjoint**. Joining is mesh
  concatenation, not a union, so overlapping members give the exact solver a
  self-intersecting operand and it deletes the body outright. Crossing grid
  grooves, and a screw shaft with its own head recess, go in separate batches.

## TODO

Confirm clearances, wall thicknesses, orientation, material shrinkage, and bed
adhesion with calibrated test prints before producing manufacturing exports.
