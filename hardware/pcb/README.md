# PCB source map

The Python source turns the reviewed board contract into native KiCad artifacts.
Edit source and reviewed data, not `generated/`. Automation lives in `tools/`.

```text
domain/      KiCad-independent electrical and physical primitives
components/  Approved parts and footprint catalog
board/       This product's definition, reviewed data, placement, and wiring
kicad/       The native KiCad adapter and routing engine
tools/       BOM, schematic, board, project, pin, and preview generators
tests/       Model, layout, SPICE, and release checks
typings/     The pcbnew API subset used by the adapter
generated/   Checked-in review and manufacturing artifacts
```

The dependency direction is `domain` → `components` → `board`; `kicad` adapts
the domain model, and `board/wiring` composes both. Only `kicad/api.py` imports `pcbnew`.

| Location | Responsibility |
| --- | --- |
| `board/definition.py`, `board/data/netlist.json` | Load the board design and its reviewed electrical connections. |
| `board/data/` | Reviewed netlist, manufacturing requirements, and KiCad project template. |
| `components/`, `components/footprints/` | Approved component implementations and physical pad geometry. |
| `domain/design.py`, `domain/connectivity.py` | KiCad-independent design, checked product access, connection objects, and indexed endpoint ownership. |
| `domain/connection_contract.py` | Resolve reviewed JSON through component-owned pin types and validate complete placement coverage. |
| `board/placement.py`, `board/square.py`, `domain/placement.py` | Product placement, repeated square assemblies, and reusable placement primitives. |
| `kicad/board.py`, `kicad/api.py` | Native board adapter and the only direct `pcbnew` import boundary. |
| `kicad/grid_router.py`, `kicad/routing_grid.py` | Deterministic routing, grid coordinates, and copper keepouts. |
| `board/wiring/` | Ordered subsystem routing, geometry, power planes, and silkscreen. |
| `domain/schematic.py`, `domain/schematic_symbols.py` | Logical sheet layout and physical-pin symbol templates. |
| `tools/` | Command implementations invoked by the `justfile`. |
| `board/artifacts.py` | Canonical generated-output paths. |

Mechanical coordinates are centred on the playing area, with the control strip
in negative Y; the KiCad board adapter handles native coordinates. Schematic pin
numbers are **physical** pad numbers, while net labels use the validated
**logical** endpoint graph. Keep those identities separate when changing symbols.

## Object ownership and types

- `BoardComponent[PinType]` owns its pin enum. `ComponentPin[PinType]` binds a
  pin to an instance; `Endpoint[PinType]` keeps that type while remaining tuple
  compatible. `ComponentInstance.model_as(Tca9554)` checks a heterogeneous board
  model before exposing product-specific operations, without casting it.
- `Connection.from_pins(name, *pins)` defines a validated electrical group.
  `CircuitBuilder.add(connection)` claims its endpoints atomically; a graph
  rejects duplicate net names and pin ownership. `BoundPin` and `EndpointResolver`
  are small structural interfaces, so different products can connect without
  erasing their pin enums into `Any`.
- `ConnectionContract` loads **only** the reviewed JSON `connections` field.
  Wiring objects select those same `Connection` objects via the graph; they do
  not maintain a second electrical truth. JSON arrays, pin strings, names, and
  no-connect booleans are checked at this boundary. No-connect KiCad names still
  use physical pad numbers, not logical aliases.
- `WiringContext.from_layout(layout)` borrows a single board's nets, pads, design,
  and graph. `WiringStage` supplies shared escaping/path application;
  `SignalTreeWiring` additionally shares node ordering and nearest-tree routing.
  Concrete subclasses contain the policies, not wrappers around procedural
  implementations. The old function entry points delegate **to** these objects.
- `ChessBoardRouter` composes stages explicitly. Hall escapes are reserved after
  control signals but before buttons/I2C; their full paths follow those buses.
  Later stages see earlier copper as obstacles, so do not reorder stages casually.
  Pure coordinate helpers remain functions; inheritance is for shared behavior,
  not a requirement to turn every utility into a class.

## Checks

From the repository root, run source checks and the unit suite without rewriting
hardware outputs:

```sh
ruff check hardware/pcb
ruff format --check hardware/pcb
pyright --project hardware/pcb/pyrightconfig.json
PYTHONPATH=hardware:hardware/pcb python3 -m unittest discover -s hardware/pcb/tests -p 'test_*.py'
```

The Pyright gate is strict for the connection/pin model, native routing adapter,
subsystem wiring, and `tests/typing_contracts.py` listed in its configuration;
it is not a claim that all older PCB modules are strictly typed. Native maps and
routing options use concrete types. `typings/pcbnew/__init__.pyi` documents the
KiCad 9 API subset we consume because SWIG's generated signatures lose those
return types; extend this boundary when adding native operations, not with `Any`
or blanket ignores. The stubs have no runtime effect. To install the analyzer
without changing project dependencies:

```sh
python3 -m venv /tmp/chess-pcb-types
/tmp/chess-pcb-types/bin/pip install pyright==1.1.411
/tmp/chess-pcb-types/bin/pyright --project hardware/pcb/pyrightconfig.json
```

Use Python 3.12 or later. Native tests need KiCad 9's `pcbnew` and `kicad-cli`;
those tests skip when unavailable. Some tests compare against checked-in generated
artifacts, so the source and artifacts must agree.

`just --justfile hardware/pcb/justfile test` also **regenerates artifacts** and runs
firmware-pin parity, ERC, and DRC. See that justfile for preview and fabrication
commands; passing the unit suite alone is not a fresh manufacturing check.
