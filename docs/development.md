# Development

Use the development container for the pinned Rust, Ruff, Blender, and KiCad 9
toolchains. From the repository root:

```sh
./tools/check
```

Individual workflows are available through `./tools/python`, `./tools/rust`,
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

CI prebuilds the development image, then runs Python, Rust, shared hardware, CAD, and PCB
validation. Use the same runners locally so local and CI behavior remain aligned.

CAD, PCB, and shared Python are linted and format-checked with [Ruff](https://docs.astral.sh/ruff/).
`./tools/python` is the repository check; `.pre-commit-config.yaml` is the same
gate for `pre-commit run`.
