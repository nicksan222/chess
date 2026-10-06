# Native KiCad board as Python

Start at [`definition/board.py`](definition/board.py): power, controls, 64 squares,
eight Hall banks, and the serpentine LED chain. `load()` returns a **pcbnew.BOARD**.
There is no parallel PCB model, geometry enum, placement aggregate, or adapter.
Python generates the board automatically; editing generated files is not authoring.

```text
definition/
  board.py, native.py, rules.py  Composition, native construction helpers, constraints
  assemblies/                   Power, controls, square, sensor-bank wiring
  parts/                        Approved native FOOTPRINT/PAD templates
  routing/                      Native routing policies and grid pathfinding
  output/                       Schematic, BOM/project, symbols, review markings
  verification.py               Open assumptions that block release (see below)
  evidence/                     Human prototype measurements (not generated)
tests/                          Focused mechanics/build checks and SPICE scenarios
generated/                      Native project, netlist, BOM, harness table, reports/previews
typings/                        Curated KiCad SWIG API signatures for strict Pyright
```

The fourth top-level folder is typing declarations only, not another implementation
of KiCad geometry. Subpackages organize responsibilities; their `__init__.py` files
do not provide wrapper APIs.

## Authoring and authority

`pcbnew` owns footprints, pads, placement, layers, nets, tracks, zones, and geometry.
Shared dimensions, approved products, pin enums, GPIO assignments and Hall-bank
mappings remain inputs from `hardware/shared/`. Small assembly handles expose shared
logical ports only. `place()` installs a native template and `connect()` assigns its
native pads from component-bound pins, rejecting duplicate ownership or reassignment.
There is no finish/freeze framework. Runtime validation checks approved products,
complete pad assignment, square membership/centres and Hall-bank wiring.

Board properties retain assembly/product intent. BOM, expanded netlist and schematic
are derived from the actual native footprints and pad assignments, not a second
connectivity graph. `generated/netlist.json` is output only. Native coordinate helpers
translate shared centre-origin/Y-up dimensions; dimension tests check against CAD.

References and historical LED net names are explicit. Native UUIDs are semantic,
reference/geometry-derived, with stable disambiguation for identical items. The
intentional one-time UUID rekey preserves physical geometry and connectivity, and
footprint paths link to generated schematic symbols. No frozen identity ledger exists.

## Component registry

`definition/parts/<component>.py` owns each native footprint and its `PcbPart`
binding: approved product, typed electronic model, library label, nominal value,
and purpose. `parts/catalog.py` only enumerates those bindings as `PCB_PARTS` for
schematic and validation code; `parts/part.py` defines the checked binding type.

Assemblies pass a typed `*_PART` entry, an explicit stable reference, position,
rotation, and assembly name to `place()`. They override `purpose` only when the role
is more specific than the product default, and `nominal_value` only for display values
such as a test point's net. Choosing a capacitor entry remains explicit. Placement
never creates a net: every connected or intentionally unused pin still appears in an
explicit `connect()` or `no_connect()` call.

Each binding also declares a `drawing_view`: whether the footprint's datasheet drawing
is seen from the connector's mounting surface (a bottom-side placement is a true KiCad
flip) or from the board top (the Pi header, whose holes are fixed by the Pi's pins and
are un-mirrored). `place(..., bottom=True)` accepts only through-hole parts with
mirror-safe pad shapes; the bottom side holds J1, J4, C1 and C140.

## Commands

Python 3.12+, KiCad 9, ngspice, Ruff 0.16.5 and Basedpyright 1.40.0 are installed
in the development container. Strict analysis covers source and tests, rejects
explicit or inferred dynamic types, and uses curated KiCad SWIG signatures. From
the repository root:

```sh
just --justfile hardware/pcb/justfile generate # Native project, schematic, BOM, DSN
just --justfile hardware/pcb/justfile check    # Non-publishing source/dimensions checks
just --justfile hardware/pcb/justfile review   # Fresh ERC/DRC, tests/SPICE, previews
just --justfile hardware/pcb/justfile pr-report main # Review + semantic Markdown diff
just --justfile hardware/pcb/justfile release  # Review + measured evidence + fabrication
```

Direct entry: `PYTHONPATH=hardware python3 -m pcb review`. Set `BASEDPYRIGHT` to
an alternate analyzer executable when needed.

**Deliberate scope reductions:** redundant architecture/accessor/snapshot tests were
removed in favor of readable dimensions and SPICE tests. PCB-to-Rust generation and
its parity plumbing were removed at user request. Firmware pin declarations in
`apps/firmware/src/hardware/pins/` are hand-maintained; there is no `pins` command.

Run retained tests without publishing: `PYTHONPATH=hardware python3 -m unittest
discover -s hardware/pcb/tests -p 'test_*.py'`. SPICE covers all squares, each button built from its pad geometry, open-drain
buses, level shifting, startup/off/approved/full-white power, a plane-mesh voltage
drop, and quiet, capture, castling, en-passant and promotion moves. Circuit files are staged under
`generated/spice/`, or temporary in standalone runs.

## Verification layers

Most checks compare the generated board with hand-typed expectations that do not import
the production tables, so an error cannot hide itself by being wrong in both places.
Evidence type for all of them is software test, SPICE or KiCad native check on the
generated design.

- **Land patterns** (`board/test_land_patterns.py`): golden pad number, centre, size,
  drill and body for every catalogued part, each with its datasheet citation, compared
  in board frame after placement rotation. A part without a cited land would be listed
  in `UNVERIFIED`.
- **Silkscreen and mask** (`board/test_silkscreen.py`): a polarity mark for every
  polarized part on its own side, and a minimum solder-mask web between vias and
  pads.
- **Decoupling** (`board/test_decoupling.py`): each IC/LED supply pin gets its own
  nearest capacitor within the board's distance rule, with ground-return and via
  checks. The limits are this board's rule; the datasheets say only "close".
- **Pin types** (`board/test_pin_types.py`): a typed table (input, output,
  open-drain, power...) catches floating inputs, open-drain nets with no pull-up,
  driver contention and rails on the wrong net.
- **Ampacity** (`board/test_ampacity.py`): IPC-2221 steady-state copper checks for
  power tracks, plane entries, the TVS fault path and device fan-outs.
- **eFuse and power path** (`spice/test_power.py`, `efuse_model.py`, `power_path.py`):
  corner-case series resistance from the harness and routed copper, a behavioural
  eFuse built from datasheet tables, over-voltage window, hot-plug, reversed plug and
  full-white cases. No vendor model.
- **Design rules and assembly checks** (`board/test_design_rules.py`,
  `test_selective_solder.py`, `test_positions.py`): the fine-pitch DRC exception
  stays scoped to the eFuse, bottom through-hole joints can be selectively soldered,
  and the pick-and-place file names each package.
- **LED rail switch and SK9822 contract** (`spice/test_led_switch.py`,
  `board/test_led_contract.py`): the rail stays off until `LED_EN`, enable ramps stay
  under the eFuse limit, and the firmware-facing frame/clock/enable constants are
  fixed in `shared/electronics/sk9822.py`.
- **Plane-mesh SPICE** (`spice/plane_mesh.py`): +5V, LED_5V and ground plane resistance from the
  real zone fill, with the LED and Pi loads at their pads.
- **Button SPICE** (`spice/test_signals.py`): the 12 buttons are
  modelled from pad geometry, so a pad mapped onto an internally strapped lead pair
  reads as permanently pressed and fails.
- **Pi header and bottom side** (`board/test_pi_header.py`, `test_bottom_side.py`): all
  40 J1 pads equal the shared transform in board frame (a mirrored header fails),
  and bottom parts keep their distance from the outline, bosses and mechanical
  keep-outs.
- **Harness as code** (`board/test_harness.py`): each JST cavity of the power and OLED
  harnesses lands on the pad, and net, listed in `shared/electronics/harness.py`.
  `generated/harness.md` is rendered from the same data.
- **I²C bus** (`spice/test_i2c.py`): bus capacitance from routed copper plus device
  loads, and rise time and sink current at the firmware's I²C rate across the OLED
  pull-up corners; fails at 400 kHz.
- **LED lines** (`spice/test_led_lines.py`): lossless-line SPICE of the AHCT125 to
  first-LED link (with and without R9) and of every LED-to-LED geometry at the supply
  corners, against the SK9822 input limits. Driver edges are assumed.
- **Firmware pins** (`board/test_firmware_pins.py`): the hand-maintained firmware
  GPIO declarations against the shared pin assignments.

**What this cannot prove.** None of it replaces a built board. Still needing bench
evidence: Hall/magnet margin, solder yield on the fine lands, harness crimps and mating,
jack plug fit and retention, button feel, inrush and fuse behaviour, supply drop, I2C
rise time at the farthest bank, LED clock integrity, Pi Wi-Fi range in the case, and
the real supply, OVLO trip points and eFuse behaviour with the real adapter.

## Review and release

Open `generated/chess-board.kicad_pro`. The schematic has an overview, power,
controls and eight bank sheets; each bank groups complete squares. Passives have
recognizable symbols; active pins carry conservative electrical roles.

`review` requires zero native ERC/DRC violations, unconnected items and schematic
parity differences, plus the retained tests/SPICE. It exports positions, SVGs and
board renders. `review.md`, `layout.json` and `manifest.json` record changes, checks,
source/tool hashes and artifact hashes for that exact build.

`pr-report` compares those fresh artifacts with a Git ref (`main` by default) and
writes `pcb-pr-report.md`. Pull-request CI uses that same recipe and maintains one
reviewer comment only when the semantic PCB design changes. It reports changed
components and fields, net endpoints, placements, nested design-rule settings,
native tracks, vias and copper zones, plus ERC/DRC counts and links to board
evidence.

Writers use a lock and sibling staging directory. Failure preserves the previous
output set; successful publication replaces the whole directory with rename rollback.
Readers never see mixed old/new files, although the directory may briefly be absent
between renames. Stale reports and fabrication exports disappear with replacement.

`release` additionally runs `build.release_gates()` **before fabrication export**: real
Hall/magnet measurements through `build.physical_evidence()`, and
`build.verification_gate()`, which refuses while `UNVERIFIED` or `ASSUMPTIONS` in
`definition/verification.py` is non-empty (design values the sources do not give, plus
mechanical's unmeasured dimensions). Both reasons are reported together. Missing
evidence deliberately blocks Gerbers and separate plated/non-plated Excellon
drills/slots, and `release` is expected to refuse today. No test skip or software
check substitutes for those measurements. See [`definition/evidence/`](definition/evidence/).

## Experimental circuit harness

`harness/` provides typed circuit declarations, reusable passive component kinds,
SPICE checks, and a KiCad board-only renderer. It is separate from the production
board in `definition/board.py`; shared hardware contracts remain authoritative.
`components/` defines the concrete board and off-board products using the harness.

Harness behavior tests are colocated `*_test.py` files. Component-specific tests
live beside their definitions in `components/`; automatic checks of the entire
catalog live in `harness/checks/`, with native KiCad checks under its `pcbnew/`
subfolder. See the [check inventory](harness/checks/README.md).

Run `just --justfile hardware/pcb/justfile harness-tests`, `component-tests`, or
`component-checks` separately. The PCB `check` recipe and root
`PYTHONPATH=hardware python3 -m unittest discover` run all three suites.
The automatic documentation gate requires network access and fails for missing
URLs, HTTP errors or invalid document responses.
The tiny divider in `harness/examples/tiny_project.py` demonstrates simulation and
project creation;
its example products are fixtures, not purchasing recommendations.
