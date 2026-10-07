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
`PackageRouting` beside the land pattern defines package escape distances,
directions, power fanout, exact package paths and scoped clearance rules.
Named package ports expose where board wiring resumes after an escape. The
harness transforms this geometry through each instance’s placement and rotation.

`catalog.py` explicitly lists all 29 PCB declarations and 12 off-board assembly
products, including the Raspberry Pi Zero 2 W, display, supply and microSD card.
Off-board products describe purchasing identity and known interfaces without
inventing PCB lands or unknown terminal order. Wire spools and harness assembly
instructions remain in the authoritative shared purchasing and harness contracts;
they are not component wrappers here.

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
Manufacturing reassessment, component 3D models, assembly
outputs and electrical/physical validation still need implementation. The old
board/test implementation has been removed; its unresolved engineering assumptions
were retained for reassessment.
