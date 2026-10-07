# CAD

## Purpose

Record mechanical source conventions and reviewed design decisions.

## Known direction

Component definitions under `hardware/cad/components` and the composed
assembly under `hardware/cad/board` are source; the `.blend`
models they produce live in `hardware/cad/generated`. Manufacturing
exports will be derived later.

The single `hardware/cad/board/generate.py` entry point uses the CAD harness to
build, validate, save and render every model atomically. Run
`just --justfile hardware/cad/justfile check` for checks and regeneration. Board
and harness tests are separate, like PCB; no legacy project discovery is required.

## Printed parts

Revision A needed 129 prints to cover a board: 64 tile lids, 64 tile trays and a
tray to hold them. The enclosure uses one case, one plate and twelve separately printable button caps.

- **`components/printable/board_case.py`** produces `Printable_Board_Case`, 344 x 404 x 30 mm,
  an open tub. The PCB drops straight into a pocket (outline plus 0.5 mm per
  side), rests on a ledge under its edge and on 20 bosses, and the Raspberry Pi
  hangs underneath it, component side up, at the shared Pi transform
  (`pi_header_pin_xy`) that also places J1. The power jack and rocker are
  panel-mounted in the back wall and wired to J4 on the board's underside.
- **`components/printable/tile_plate.py`** produces `Printable_Tile_Plate`, 335 x 395 mm,
  covering the whole board: the checkerboard engraved over the playing area with
  a through-window over each LED and an 18 × 18 mm square ring channel around a retained 14 × 14 mm island above each sensor, and the control bezel (twelve button holes,
  the raised bezel for the larger display) over the strip. It rests on the case rim
  outboard of the PCB pocket.

The bezel belongs to the plate rather than the case so that the board can be
lowered in from above: with a fixed bezel, the button stems that pass through it
would stop the board going in.

`board/board.py` composes the assembly. The harness imports both exact owning
meshes and imports the checked KiCad `chess-board.glb` assembly, including its
substrate, mounting holes, copper, artwork and package-local STEP models. All 327 component placements are represented, along with the
host board and display. It does not recreate printable geometry or rely on stale
PCB position exports. CAD refreshes stale PCB exports automatically; source and
artifact fingerprints prevent mixing revisions. Component model fidelity is
recorded in `3d-models.json`; dimension-based envelopes remain simplified.

The case is deeper than it is wide by exactly the 60 mm control strip. Putting
the buttons and the display on a face-up strip at the front of the same PCB is
what keeps every component on one side of the board and avoids right-angle parts.

## Coordinates and the assembly datum

Coordinates are centred on the **playing area**, not the case, so square centres,
LED positions and Hall-sensor positions stay symmetric about the origin while the case
carries `CASE_CENTER_OFFSET_Y_MM`.

All printable parts are generated in **assembly coordinates**: the case floor at
z = 0, the plate occupying the top 3 mm. `board-assembly` therefore moves neither
of them. That is deliberate — if the plate ever stops meeting the case, it is a
real error in `hardware/shared/dimensions/` rather than a positioning mistake in a view, and
the render shows it.

## Shared measurements

Shared CAD measurements live in `hardware/shared/dimensions/`, grouped by
board, case, panel, and tile plate. The package validates itself on import. Among other things it checks that the internal stack
— floor, Pi cavity, board, gap, plate — sums exactly to the case height, that
the board fits its pocket and the ledge carries every edge however the board
floats, that every plate screw lands on the rim rather than over the PCB, that
button stems stand 0.5-2.0 mm proud of the bezel, that no
support boss collides with an LED or a Hall sensor, and that every control-panel feature
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

The two enclosure parts are larger than a desktop printer bed: the case spans
404 mm and the plate 395 mm, so they are quoted from an FDM print service.
The twelve button caps fit a desktop printer.
`REFERENCE_DESKTOP_BUILD_VOLUME_MM` exists to state that rather than to gate
anything, and the tests assert that neither enclosure part fits it. An edge margin is
reserved before testing whether a part fits.

The plate's underside is pocketed square by square, leaving ribs on the grid
lines. A 3 mm solid sheet 320 mm across is a lot of material to have quoted and a
warping risk; the pockets remove about a third of it and double as the clearance
over the Hall sensors.

## Validation

Pure Python tests run in CI without Blender. During local regeneration,
`harness/base/blender/validation.py` additionally rejects non-manifold or zero-volume FDM meshes
and checks each generated part's measured bounding box against its build
envelope.

Two Blender-specific traps are guarded in `harness/base/blender/modeling.py`, because both fail
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

## Piece placement and visible controls

Each square has an 18 × 18 mm square ring channel, 0.8 mm deep relative to its
own surface, surrounding a 14 × 14 mm center island. The island remains at the
square's surface level, elevated relative to the channel floor. Solid 19.6 × 19.6 mm
underside supports preserve the floor above the Hall sensors. The shared interface
for future pieces is a square ring foot, 17.5 mm outside and 14.5 mm inside,
projecting 0.6 mm below the base. Pieces lift out freely without a mechanical latch.
Their magnet pockets and physical sensing margin remain to be designed and tested.

The LEDs are exposed by 4.6 mm square through-windows. The control strip is
lowered 1 mm. The D-pad is on the left, OK beside the centered display, function
buttons on the right and Reset separated from them. Shared button identities
supply PCB switch positions, CAD placement, render labels and GPIO assignments.

The 2.42-inch MC242GW screen is exposed through a raised bezel. The module's
carrier rests on four mounting ledges with blind screw pilots and four top access holes; screen, frame,
carrier holes and solder pads follow the supplier drawing. Omit the supplied
upright header and solder the four 180 mm harness wires directly to pins 1–4;
RES remains open for onboard power-on reset. Print tolerances, screws, cap
retention and real wire dressing still require a physical prototype.

The OLED mount uses four [M2.5 × 3 DIN 912 socket screws](https://www.newstarfastenings.com/en-gb/products/m25-x-3-socket-cap-screw-din-912-steel-129-self-finish),
with 4.5 mm heads and a 2 mm hex driver. The bezel's 5 mm access holes allow
installation from above. Calibrate/drill and tap the printed 2 mm pilots to M2.5
before installing the carrier; verify thread holding and screw-tip clearance on
a prototype. Screw models are not included in the electronics envelope render.
