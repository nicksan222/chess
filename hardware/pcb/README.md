# PCB authoring

The PCB has three source folders:

- `components/`: one concrete component per file, including its purchasing facts,
  land pattern and named connections to physical pins.
- `harness/`: reusable circuit declarations, SPICE conversion, native KiCad
  rendering and automatic component checks. KiCad type stubs live in
  `harness/typings/`.
- `board/`: just `board.py` (components, placement, layout and rules),
  `wiring.py` (copper intent), and `generate.py` (the single output pipeline).
  `board/tests/` holds specific electrical behavior tests using the harness.

`generated/` contains output, not source. Generate inside the devcontainer:

```sh
just --justfile hardware/pcb/justfile generate
# or
PYTHONPATH=hardware python3 -m pcb.board.generate
```

Open `generated/chess-board.kicad_pro` in KiCad. Generation writes the PCB,
connection schematics, BOM, expanded netlist, placement CSV, PDF/SVG/PNG previews,
ERC/DRC findings, a native `chess-board.glb` assembly, portable component STEP
models, `3d-models.json` provenance/fidelity, a manifest, and `chess-board-fabrication.zip`. The ZIP contains
all eight copper layers, masks, silkscreens, outline, paste layers and separate
plated/non-plated Excellon drill files. It validates exported schematic pin maps and
schematic/PCB parity before atomically replacing previous output.

The board owns its eight-layer stackup, four rail planes, mounting holes and
silkscreen in `board/board.py`. `board/wiring.py` declares routing intent with
`NetRoute` records (layer choices, widths and local areas); the harness supplies the obstacle-aware
multilayer router. Exact paths use `CopperPath` through named component pins.
`RoutingPlan` orders power connections, LED links and signal routes; execution lives entirely
in the harness. Package escape geometry and local clearance rules belong to each
component definition. There is no native routing implementation under `board/`.
Connections come from the components' pin maps. Generation checks native routed connectivity
and exports full-board copper SVGs and matching PNGs (using `rsvg-convert`).
`board-connections.svg` remains a separate logical airwire view.
Board pytest tests run ngspice against actual sensing and button components and
their pin maps. They cover every square, piece placement/removal, a move between
banks, startup bypass charging, crossed inputs, individual button presses,
three simultaneous presses, all buttons held, bounce and release. Button checks
explicitly supply an external 3.3 V bias through a declared source resistance;
this represents host GPIO pull-ups, not additional PCB components or guaranteed
Pi pull-up limits. Both `check` and generation collect all board tests with pytest.
Generation writes `electrical-checks/results.json`, `junit.xml` and `tests.log`;
failed, skipped or empty suites stop the export. Run them directly with
`python3 -m pytest hardware/pcb/board/tests` inside the devcontainer.
The models are ideal: magnetic margins, sensor sampling delay, I2C, firmware
debounce and electrical behavior outside the sensing/button circuits remain untested.

```sh
just --justfile hardware/pcb/justfile check          # lint, types, harness/catalog checks
just --justfile hardware/pcb/justfile review         # check, then generate authoring output
just --justfile hardware/pcb/justfile harness-tests
just --justfile hardware/pcb/justfile component-tests
just --justfile hardware/pcb/justfile component-checks
just --justfile hardware/pcb/justfile pr-report main
```

Automatic checks live in [harness/checks/](harness/checks/README.md). Documentation
checks use real HTTP requests. Shared products, dimensions and electrical
contracts in `hardware/shared/` remain authoritative.

Pin electrical roles, reassessed manufacturing constraints,
detailed supplier geometry, active-device simulations and physical evidence are still
pending. Previous engineering assumptions are retained in
[engineering assumptions](../../docs/pcb-assumptions.md) for reassessment, not as proof of
the new design. Fabrication files are generated locally for review; manufacturing
approval remains pending. The separate release command still refuses approval.

Repeated components are created in loops as separate instances. Select them by
square or bank: `board.sensors["A1"]`, `board.leds["H8"]`,
`board.sensor_bypasses["A1"]` or `board.sensor_banks["A1-D2"]`.
Their own pin maps remain the source of electrical connectivity. Routing can be
changed for one sensor without defining another component or reconnecting it:

```python
from dataclasses import replace
from shared.electronics.hall_sensor import HallSensorPin

sensor_net = board.sensors["A1"].net(HallSensorPin.ACTIVE_LOW_OUTPUT)
board.wiring = tuple(
    replace(route, width_mm=0.4) if route.net == sensor_net else route
    for route in board.wiring
)
```


The 3D pipeline is owned by the PCB harness. `ComponentDefinition.model_3d`
optionally declares package-local colored solids. Other products receive an
explicitly labeled envelope from their existing body dimensions. CadQuery writes
one STEP per product; the harness attaches `${KIPRJMOD}/models/...` references to
native footprints. KiCad then supplies board-side placement, rotation, mounting
height, holes, copper and artwork in the GLB. Missing component meshes fail the
export. CAD imports that exact artifact instead of maintaining electronic bodies.
These models do not claim supplier detail or physical manufacturing validation.

The PCB export also owns `pcb-components.json`: component bodies, mating envelopes,
contact positions and named sensor/LED/control groups for the Blender bridge.
`3d-models.json` binds that snapshot, native PCB and GLB to source and exporter
version fingerprints. Portable `Model3D`, `Solid3D` and `MatedZone` values are
available through `pcb.harness`; native conversion stays under `pcbnew`.

Assembly review outputs include `assembly-bom.csv` (grouped quantities, MPNs and
mounting types), `assembly-smd.csv` and `assembly-through-hole.csv` (disjoint
placement lists). `positions.csv` retains native XY/rotation conventions and adds
package identity from component definitions. `harness.md` and `harness-bom.csv`
cover the separate off-board wire assemblies. See `generated/assembly.md` for
assembler interpretation and the outstanding release requirements.
