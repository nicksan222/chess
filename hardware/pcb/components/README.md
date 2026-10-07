# Board components

Each component has one plainly named file beside its tests. Folders describe
actual component types: `resistors`, `capacitors`, `mosfets`, `leds`,
`hall_sensors`, `gpio_expanders`, `level_shifters`, `logic_gates`, `tvs_diodes`,
`connectors`, `switches`, and `power`.

PCB component constructors accept named electrical connections and own the
mapping to physical pins. For example, `LedPowerMosfet` accepts `source`, `gate`
and `drain`, then assigns all three internally joined source pins and all four
drain pins itself. Callers do not write a separate pin map or wiring layer.
References, purposes and placements belong to each instance; purchased part
numbers, values and land patterns are fixed by its component file.
`PackageRouting` beside the land pattern defines package escape distances,
directions, power fanout, exact package paths and scoped clearance rules.
Named package ports expose where board wiring resumes after an escape. The
harness transforms this geometry through each instance’s placement and rotation.

`catalog.py` explicitly lists all 29 PCB declarations and directly references the
12 shared `ComponentSpec` records for off-board assembly products, including the
Raspberry Pi Zero 2 W, display, supply and microSD card. Off-board products have
no PCB wrapper classes: their purchasing identities and known interfaces stay in
the shared contracts without invented PCB lands or terminal order. Wire spools
and harness assembly instructions likewise remain in the authoritative shared
purchasing and harness contracts.

Shared products and pin identities remain authoritative. `board/board.py`
composes these components using the harness; component and automatic catalog
checks no longer depend on the removed implementation. The Pi socket's courtyard
includes the shared body envelope. Capacitor land assumptions remain unverified
as documented in `docs/pcb-assumptions.md`.

Resistors and capacitors have ideal simulation models. Hall sensors have an ideal
occupancy-controlled open-drain model; GPIO expanders model their pulled-up
sensing inputs. These do not model magnetic margins or I2C protocol behavior.
Other unsupported components reject simulation explicitly.

Harness behavior tests live beside their implementation. Component-specific
checks live beside definitions; automatic catalog and native KiCad checks live
in [harness/checks/](../harness/checks/README.md). Datasheet checks require network
access and reject missing or unavailable documentation URLs.

## Current status

All PCB component instances and their connections are composed by `Board`.
KiCad project, schematic, BOM, netlist and previews are generated from it.
Every product now has a generated STEP model attached to its native footprint.
Component-specific `model_3d` solids or dimension-based envelopes feed KiCad’s GLB
assembly; fidelity is recorded explicitly. Detailed supplier models, manufacturing
reassessment and electrical/physical validation remain pending. The old
board/test implementation has been removed; its unresolved engineering assumptions
were retained for reassessment.
