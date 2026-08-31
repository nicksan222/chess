# Development

Use the development container for the pinned Rust, Blender, and Gerbonara
toolchains. From the repository root:

```sh
./tools/check
```

Individual workflows are available through `./tools/rust`,
`./tools/shared-hardware`, `./tools/cad`, and `./tools/pcb`.

## Hardware domains

`hardware/shared` contains tool-independent dimensions, component specifications,
and wiring. `hardware/cad` adapts the physical contract into Blender models.
`hardware/pcb` owns electrical connectivity, footprints, placement, routing, and
fabrication output. There is no separate schematic domain.

The PCB's reviewed sources are `hardware/pcb/design/netlist.json` and `bom.md`.
Generation validates those sources against every footprint and copper connection.
CAD and PCB both consume `hardware/shared`, preventing the mechanical and
electrical layouts from independently copying dimensions or mappings.

Outside the container, runners create ignored caches under `.cache`. Generated
artifacts remain under each domain's `generated/` directory.

## CI

CI prebuilds the development image, then runs Rust, shared hardware, CAD, and PCB
validation. Use the same runners locally so local and CI behavior remain aligned.
