# PCB checks

Run without publishing:

```sh
PYTHONPATH=hardware python3 -m unittest discover -s hardware/pcb/tests -p 'test_*.py'
```

`just --justfile hardware/pcb/justfile review` regenerates, checks and publishes the
complete native review set, including the SPICE circuits; KiCad and ngspice are
required. Evidence type for everything here is a software test, SPICE or a KiCad
native check on the generated design. None of it proves a physical board works; see
the bench list in the [PCB README](../README.md#verification-layers).

Many board tests read the freshly generated `netlist.json`, `positions.csv` or
`chess-board.kicad_pcb` (from `PCB_OUTPUT` when set, else `generated/`), and compare
them with expectations typed by hand from datasheets, so a mistake cannot hide by
being wrong in both the code and its test.

## `board/`

- `test_contract.py`: golden pin-level connectivity of the generated netlist (Hall
  squares to expander inputs and addresses, LED chain order, I2C, buttons, power path).
- `test_land_patterns.py`: every catalogued part's pads, drills and body against
  cited datasheet rows, in board frame after placement; part-by-part drawing view.
- `test_pin_types.py`: electrical type per logic pin: no floating input, no undriven
  open-drain net, no contention, rails on the right net.
- `test_decoupling.py`: each IC/LED supply pin has its own nearby capacitor, with
  ground-return and via checks.
- `test_ampacity.py`: IPC-2221 steady-state copper capacity of power tracks, plane
  entries, the eFuse path (maximum flow through the routed copper, `copper_flow.py`),
  the TVS fault path and device fan-outs.
- `test_silkscreen.py`: polarity marks on every polarized part, and solder-mask webs.
- `test_pi_header.py`: all 40 J1 pads sit under the matching Pi pin; a mirrored
  header is reported.
- `test_bottom_side.py`: bottom-side parts (J1, J4, C1, C140) keep their distance from
  the outline, support bosses and panel keep-outs.
- `test_harness.py`: each power/OLED harness cavity lands on the pad and net named in
  `shared/electronics/harness.py`.
- `test_design_rules.py`: the generated `.kicad_dru` fine-pitch exception stays scoped
  to U74 (the eFuse); DRC without it flags only U74 items.
- `test_positions.py`: the pick-and-place file names every part's package.
- `test_selective_solder.py`: bottom-side through-hole joints keep their distance
  from top-side SMD pads and courtyards so they can be selectively soldered (3 mm rule,
  fab to confirm).
- `test_led_contract.py`: the firmware-facing SK9822-A contract in
  `shared/electronics/sk9822.py` (end-frame length, 10 MHz clock limit, blank frame and
  enable sequence constants).
- `test_dimensions.py`: board envelope and orientation, squares and banks, panel
  parts, courtyards and pads against the shared dimensions.
- `test_routing.py`: the grid router's boundaries and determinism on a synthetic board.
- `test_native.py`: native identities are stable; duplicate references and pin
  reassignment are rejected.
- `test_power_budget.py`: the approved LED limit against the 2 A supply and fuse.
- `test_firmware_pins.py`: the hand-maintained firmware GPIO constants against the
  hardware pin assignments (read-only).
- `test_verification.py`: `verification_gate()` lists every open item and passes only
  when `UNVERIFIED` and `ASSUMPTIONS` are empty.

## `pipeline/`

- `test_build.py`: atomic publication, source-change detection, native-report failure,
  and the release gates (physical evidence plus verification refuse together, and
  no fabrication export runs when either fails).
- `test_bank_assemblies.py`, `test_led_link_names.py`: published references,
  addresses, positions and net names stay stable.
- `test_pr_report.py`: the semantic PR report describes design changes.

## `spice/`

See [`spice/README.md`](spice/README.md): power path, eFuse and LED-rail-switch corners, signals, I²C bus timing, LED line
edges and piece-movement scenarios built from the real board's pads and nets.

## Release gate

`just --justfile hardware/pcb/justfile release` first runs everything above, then
refuses unless both the real Hall/magnet evidence (`build.physical_evidence()`) and an
empty `ASSUMPTIONS` list (`definition/verification.py`) are present. It is expected to
refuse until that physical and sourcing work is done; no test skip substitutes for it.
