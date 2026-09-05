# PCB source map

The Python source turns the reviewed board contract into native KiCad artifacts.
Edit source, not `generated/`; the root scripts remain the command-line entry points.

| Location | Responsibility |
| --- | --- |
| `board/definition.py`, `board/netlist.json` | Load the board design and its reviewed electrical connections. |
| `components/`, `components/footprints/` | Approved component implementations and physical pad geometry. |
| `base/design.py`, `base/connectivity.py` | KiCad-independent design, checked product access, connection objects, and indexed endpoint ownership. |
| `base/connection_contract.py` | Resolve reviewed JSON through component-owned pin types and validate complete placement coverage. |
| `base/board_placement.py`, `base/placement.py`, `base/square.py` | Placement rules, ownership checks, and repeated square assemblies. |
| `base/kicad/board.py`, `base/kicad/api.py` | Native board adapter and the only direct `pcbnew` import boundary. |
| `base/kicad/grid_router.py` | Route bounds, deterministic path search, and track/via creation. |
| `base/kicad/routing_grid.py` | Grid coordinates and copper-to-raster keepouts; vias must clear every copper layer. |
| `board/wiring/context.py`, `board/wiring/router.py` | Borrowed native state, the routing-stage interface, and ordered composition. |
| `board/wiring/signal_tree.py`, `board/wiring/controls.py` | Shared host-rooted tree behavior; control signals and I2C specialize reservation/layer policy. |
| `board/wiring/power.py`, `led.py`, `sensors.py`, `buttons.py` | Subsystem wiring objects own their copper policies; Hall wiring retains reservations across stages. |
| `board/wiring/geometry.py` | Mechanical outline, mounting holes, power planes, and native serialization. |
| `board/wiring/silkscreen.py` | Playing-grid dots, connector pinouts, and bring-up labels. |
| `base/schematic.py` | Sheet layout and logical net/no-connect labels, without native KiCad dependencies. |
| `base/schematic_symbols.py` | Physical-pin symbol templates, product metadata, and stable KiCad UUIDs. |
| `write_schematic.py` | Default board selection and schematic/symbol-library file writing. Existing rendering imports remain available here. |
| `board/artifacts.py` | Canonical output paths used by the generation scripts. |

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
