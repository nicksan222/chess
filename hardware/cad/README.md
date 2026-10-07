# Mechanical design

CAD follows the PCB domain: concrete components, one composed board, a reusable
harness and generated output. Shared dimensions remain in `hardware/shared`.

```
components/  one physical component per file; printable parts and electronics
board/       Board definition, the single generate.py entry point, specific tests
harness/     registry, Blender geometry/rendering, validation and automatic checks
generated/   owning .blend models, assembly, PNGs and verification manifest
```

`board/board.py` owns the case, plate, imported PCB assembly, off-board host and
OLED, rear jack, rocker, mating plug envelopes and all eight harness conductors. Repeated PCB parts remain individually selectable by square or control name:
`board.sensors["A1"]`, `board.leds["H8"]`, `board.buttons["OK"]`.
The PCB generator attaches package-local STEP models and exports `chess-board.glb`.
Blender imports that file's substrate, holes, copper, artwork and component meshes;
it does not rebuild PCB electronics. Component references survive as `PCB_SW1`,
`PCB_SW1_Body`, etc. Package geometry and model fidelity belong to PCB definitions.
Most models are explicitly dimension-based envelopes; the switch has its declared
housing and actuator. Detailed supplier CAD and physical validation remain pending.

Shared supplier dimensions, mounting interfaces and layout measurements remain
readable source definitions. CAD uses them for enclosure fits and off-board
parts; it does not infer these values from imported Blender mesh bounds.

There are fourteen printed parts: twelve button caps plus the case and plate. `components/printable/board_case.py` owns the
344 × 404 × 30 mm open case; `tile_plate.py` owns the 335 × 395 mm checkerboard
and control bezel, including its raised screen and underside mounting ledges. Their cuts, supports, screw positions and assembly coordinates
retain their positions. Each square has an 18 × 18 mm square ring channel,
0.8 mm deep, surrounding a 14 × 14 mm island at the square's original surface
height. A solid 19.6 × 19.6 mm underside support covers the Hall sensor and
reinforces the channel floor. Future pieces use a matching square ring foot:
17.5 mm outside, 14.5 mm inside, projecting 0.6 mm below the base. Both interfaces
come from `shared/dimensions/tile_plate.py` and include clearance on both sides.

Each LED has a 4.6 mm square through-window above its actual emitter position.
Controls use a left D-pad, separate OK, a right function group (F1-F5 and PASS),
and an isolated Reset. Positions and render legends read the same shared button
identities used by the PCB and GPIO mapping; moving switches requires regenerating
both PCB and CAD; CAD generation automatically refreshes a stale PCB export.

The 60 mm control strip is recessed 1 mm. A 2.42-inch MC242GW monochrome OLED
uses the same four-wire I²C interface and 128 × 64 graphics API. The module's
supplied pin header is omitted: solder the harness directly, leaving RES open
for the module's onboard reset circuit. Its screen sits above the panel in a
bezel, with four carrier mounting ledges and blind screw pilots and four top access holes. Carrier, glass,
mounting holes and underside envelopes follow the supplier drawing. Screw size,
print tolerances and retention still require a physical prototype.

Twelve separate printable caps fit the existing TL1105 switch stems. Their
labels are recessed into the actual panel mesh. D-pad, OK, function buttons,
PASS and RESET share their coordinates with the PCB and GPIO definitions.
The four OLED conductors remain 180 mm long with dressing/service slack.
Square faces and locating channels use charcoal and ivory presentation materials.
The assembly imports those exact meshes rather than rebuilding
them. Coordinates are centered on the playing area; PCB coordinates are translated
once on the imported KiCad assembly, converting glTF metres to our millimetre scene.

## Generate and check

```sh
just --justfile hardware/cad/justfile check-fast  # lint, types and Python tests
just --justfile hardware/cad/justfile generate    # complete models and renders
just --justfile hardware/cad/justfile check      # both
```

`board/generate.py` checks PCB/shared source fingerprints, actual exporter versions,
and hashes of the saved PCB, GLB and PCB-owned `pcb-components.json`. CAD source
provenance includes its `justfile` and the shared `hardware/build_support.py` publisher.
The selected Blender executable is queried directly and publication verifies that the
worker recorded the same runtime version. Missing, altered or stale output triggers the full checked PCB pipeline.
All expected component references must have meshes in the GLB. The current export,
its `3d-models.json` fidelity/provenance report, and its validated metadata snapshot
cross the host Python / Blender Python 3.11 boundary. Run inside the devcontainer,
which supplies KiCad, CadQuery 2.6.1 for STEP generation, and Blender 4.5.

`just generate` and CI run PCB review before CAD, using the same checked export.
The standalone CAD command refreshes that dependency only when needed. CI runs
one sequential hardware job and retains separate successful PCB and CAD outputs.

The generator builds the case, builds the plate, assembles their saved models,
checks fit, renders the finished/open views and writes `manifest.json`. It publishes
one complete artifact set atomically; a failed model, render, check or missing output
leaves previous output untouched. Do not hand-edit generated files.

Board-specific dimension/instance tests live in `board/tests`. Generic registry,
publication and clearance checks live in `harness`, including negative regressions.
Every build checks actual PCB body heights, connector mating envelopes, case/bay
clearance, positive/manifold printable meshes, build volume and seated assembly fit.
The fit manifest records measured mesh dimensions, volumes and intersection results.
`board/tests/blender` runs inside the generation worker on the actual seated meshes,
checking all 64 square seats and LED windows, the lowered strip, button protrusion,
display sight line and render visibility. Electronics tests check actual positions,
rotations, mounting sides and body dimensions of every PCB instance, plus the
shared host/display dimensions, plus native PCB mounting holes and artwork.
The importer welds coincident shading vertices without moving the surface and
requires closed positive-volume solids before intersection checks. The worker saves
the finished inspection view, reopens that exact `.blend`, and only then runs the
native tests. Host pytest skips these native tests; every generation must run them
without skips before it publishes.

## Blender harness

`harness/base/blender` owns mesh operations, materials, studio setup, saving and
rendering. Boolean batches require disjoint cutters, and bevel radii must stay
below half the thinnest dimension: these prevent silent invalid geometry.
Materials are presentation choices rather than manufacturing specifications.

The pinned Blender toolchain uses a private Xvfb display when available. The
`setup` recipe can download a checksum-verified build into `.cache` outside the
container; `BLENDER_BIN` selects an existing installation. Ruff and strict
Basedpyright use Blender stubs; normal declarations and checks run without Blender.

Both printed parts exceed desktop printer beds and are intended for an FDM service.
Mesh checks do not prove shrinkage, supports, layer adhesion or physical operation.
Calibrated prints and physical clearance review remain pending; generated models
are review artifacts and do not constitute manufacturing approval.

The PCB generator owns the metadata snapshot as well as the meshes. CAD only
copies and reads the checked bundle; it validates the copied files and retries
once if concurrent PCB publication interrupts the copy. The frozen input GLB is
retained with the CAD outputs so the assembly can be reviewed independently.
`manifest.json` fingerprints CAD/shared source inputs and hashes every output,
including the snapshot. Atomic publication rejects missing or altered artifacts.

Rear power components and mating plugs use simplified dimension envelopes.
Every harness conductor retains its connector cavity, net, cut length and
proposed route length. Mesh checks cover enclosure, PCB and off-board collisions,
except same-reference solids and declared mating interfaces. An AABB broadphase
selects possible collision pairs before mesh booleans; remaining checks use a
0.01 mm³ numerical-noise tolerance, with connector endpoint allowances applied only
at their declared mating interfaces.
Unmodeled service slack, actual solder-pad locations on the OLED, cable bend radii,
connector latches and final wire dressing remain physical assembly checks.

The OLED mount uses four [M2.5 × 3 DIN 912 socket screws](https://www.newstarfastenings.com/en-gb/products/m25-x-3-socket-cap-screw-din-912-steel-129-self-finish),
with 4.5 mm heads and a 2 mm hex driver. The bezel's 5 mm access holes allow
installation from above. Calibrate/drill and tap the printed 2 mm pilots to M2.5
before installing the carrier; verify thread holding and screw-tip clearance on
a prototype. Screw models are not included in the electronics envelope render.
