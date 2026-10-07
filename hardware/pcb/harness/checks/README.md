# Automatic component checks

This folder states the checks that apply to every declared component. Component
authors define products, lands and internal pin mappings in `pcb/components/`;
they do not repeat these checks in each component file.

There are three distinct suites:

| Suite | Location | What it proves |
|---|---|---|
| Harness behavior | Colocated `*_test.py` under `harness/` | Validation, rendering and simulation behave correctly, including deliberately invalid fixtures |
| Component-specific behavior | Colocated `*_test.py` under `components/` | A particular component has the expected pin map, dimensions, fixed value and purchasing identity |
| Automatic declaration checks | `test_*.py` in this folder | Every catalog entry satisfies the common checks below |

## Check inventory

| Check | Entry point | Input |
|---|---|---|
| Catalog completeness and uniqueness | `test_catalog.py` | All PCB definitions and assembly products against the authoritative shared catalog |
| Datasheet coverage and availability | `test_datasheets.py` | Every purchasing product, including wire spools, and every PCB product reference |
| Native pad coverage, net assignments, closed courtyards, copper containment and save/reload preservation | `pcbnew/test_components.py` | Every PCB definition rendered and reopened on both sides at 0°, 90°, 180° and 270° |

`catalog.py` is the board-specific adapter. Reusable checks take explicit inputs:
`datasheets.check_all(references)` checks unique URLs once;
`pcbnew.board.validate_board(registry, native_board)` compares a rendered board
with its actual component registry. The native renderer calls the latter before
returning or saving a board. Registry validation also checks declared courtyard
overlap, board-edge containment, complete pin assignments and explicit peer
connections. An intentional unused pin must have an explained `NoConnect`.

During generation, `pcbnew.netlist.apply_netlist` compares KiCad’s exported
physical terminal map with the circuit, including repeated pads and intentional
no-connects. A mismatch fails before any PCB edits. It then copies KiCad’s unused
pin net names onto their PCB pads. `pcbnew.reports.check_schematic_parity` checks
the saved project against KiCad’s DRC parity results before previews are exported.

Board electrical scenarios were removed; new checks will use the harness. Generic behavioral-program
execution and coverage reporting live in `harness/base/spice/render/`; their
negative controls ensure missing measurements, exceeded limits and unavailable
fixtures cannot pass silently. `pcbnew.routing.require_routed_copper` blocks
models that need routes or filled planes when those inputs are absent.

The catalog native sweep exercises each footprint in isolation. It checks that
pads receive their declared nets; it cannot prove that traces connect pads on a
complete routed board. Production KiCad DRC remains the gate for unrouted pads
and copper clearances. The previous-implementation parity test was removed with that implementation.

Harness negative controls deliberately remove or duplicate footprints, corrupt pad
numbers and nets, connect an intentional no-connect, erase pad copper, move pads
outside the courtyard, and break courtyard closure, size, side or edge order.
Local HTTP fixtures exercise redirect loops, missing redirect targets, invalid
schemes, PDF-to-HTML redirects and error responses without external requests.

The documentation gate performs GET requests with redirects, bounded concurrency
and timeouts. Missing URLs, HTTP errors, empty responses, false PDFs, common
soft-404 titles and access challenges fail. It never silently skips an inaccessible
site. Some sources are manufacturer-authored PDFs hosted by distributors because
the manufacturer's site blocks automated access. Availability does not verify
part identity or document revision; those still require engineering review.

## Commands

Run from the repository root in the development container:

```sh
just --justfile hardware/pcb/justfile harness-tests
just --justfile hardware/pcb/justfile component-tests
just --justfile hardware/pcb/justfile component-checks
just --justfile hardware/pcb/justfile datasheets
just --justfile hardware/pcb/justfile check
```

The first two commands need no external network. `component-checks` includes live
documentation requests. `check` runs the three suites, board-specific tests from `board/tests/`, lint/type checks and the
composed board declaration; review, CI and the commit gate use it too.
Root `PYTHONPATH=hardware python3 -m unittest discover` also discovers these
suites once. The normal gate requires KiCad and ngspice from the devcontainer.
