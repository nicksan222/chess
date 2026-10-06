# Board components

Each component has one plainly named file beside its tests. Folders describe
actual component types: `resistors`, `capacitors`, `mosfets`, `leds`,
`hall_sensors`, `gpio_expanders`, `level_shifters`, `logic_gates`, `tvs_diodes`,
`connectors`, `switches`, `power`, and `modules`.

PCB component constructors accept named electrical connections and own the
mapping to physical pins. For example, `LedPowerMosfet` accepts `source`, `gate`
and `drain`, then assigns all three internally joined source pins and all four
drain pins itself. Callers do not write a separate pin map or wiring layer.
References, purposes and placements belong to each instance; purchased part
numbers, values and land patterns are fixed by its component file.

`catalog.py` explicitly lists all 29 PCB declarations and 12 off-board assembly
products, including the Raspberry Pi Zero 2 W, display, supply and microSD card.
Off-board products describe purchasing identity and known interfaces without
inventing PCB lands or unknown terminal order. Wire spools and harness assembly
instructions remain in the authoritative shared purchasing and harness contracts;
they are not component wrappers here.

Shared products and pin identities remain authoritative. The existing production
board generator still uses `definition/parts`; its migration is separate. The harness-owned
catalog checks compare native copper and pad process settings against those parts.
The Pi socket's courtyard includes the shared body envelope, oriented along its
40-pin land pattern. Capacitor land assumptions remain unverified as documented
in `definition/verification.py`.

Resistors and ceramic capacitors use the harness's ideal simulation models. The
polarized bulk capacitor has an ideal capacitance model only. Other components
have no simulation model: requesting SPICE for them fails explicitly.

Run `PYTHONPATH=hardware python3 -m unittest discover -s hardware/pcb/components
-p '*_test.py' -t hardware`, or use the PCB package's `check` recipe.

## Automatic checks

Checks applying to all components live in
[`../harness/checks/`](../harness/checks/README.md), including its dedicated
`pcbnew/` suite. This folder keeps the transparent definitions and their specific
pin-map/value/geometry tests. The normal PCB gate runs both suites, and new catalog
entries automatically receive the common checks.

All approved products now have documentation URLs, including the wire spools in
the shared purchasing catalog. Missing URLs and unavailable documents fail the
automatic documentation gate. Run `just --justfile hardware/pcb/justfile datasheets`
for an audit; it performs real GET requests and therefore needs network access.
URLs come from the authoritative shared product records, so a repaired link is not
copied into every component definition. The [availability audit](datasheet-audit.md)
records the checked URLs and document revision limitations.

## Migration status

All 29 PCB part kinds and 12 off-board products have concrete declarations here.
The production board is **not migrated**: `definition/board.py` still composes the
legacy assemblies and `build.py` routes and exports that native design.

Remaining work:

- Express the full board's instances, placements and inter-component connections
  as a harness circuit, including squares, Hall banks, LED chain and controls.
- Preserve the production layer stack, zones, mechanical features, design rules,
  footprint fields, fabrication markings and routing behavior in the new path.
- Connect the new design to schematic/BOM/netlist output, native ERC/DRC,
  existing board/SPICE regressions and release evidence gates; compare the full
  generated design before retiring the legacy part and assembly implementations.
- Add appropriate active-device simulation models where useful. Currently only
  passive ideal models are available; off-board classes describe product facts
  and interfaces, not a connected assembly simulation.
- Reconcile document/product revisions. The OLED vendor document linked during the audit describes a
  28x33 mm module while the shared product records 27x27 mm; geometry remains
  unchanged pending reconciliation.
