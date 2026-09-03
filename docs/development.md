# Development

Use the development container for the pinned Rust, Ruff, Blender, KiCad 9, and
Just toolchains. From the repository root:

```sh
just check
```

Run `just --list` for repository-wide capabilities. Every application, crate,
and hardware domain owns a `justfile`; run one directly to see and invoke only
that package's capabilities:

```sh
just --justfile hardware/pcb/justfile --list
just --justfile hardware/pcb/justfile review
just --justfile crates/chess/justfile check
just --justfile apps/firmware/justfile image-check
```

The root `justfile` only composes these package-owned recipes. Implementation and
package policy stay beside the code they operate on.

## Hardware domains

`hardware/shared` contains tool-independent dimensions, component specifications,
and wiring. `hardware/cad` adapts the physical contract into Blender models.
`hardware/pcb` owns electrical connectivity, footprints, placement, routing, and
fabrication output. There is no separate schematic domain.

The PCB's reviewed sources are `hardware/pcb/board/netlist.json` and the
component catalog. Generation validates them against every footprint and copper
connection, then writes the BOM under `hardware/pcb/generated/`. CAD and PCB
both consume `hardware/shared`, preventing the mechanical and electrical layouts
from independently copying dimensions or mappings.

Generated artifacts remain under each domain's `generated/` directory. The CAD
recipe creates an ignored fallback toolchain under `.cache/blender` outside the
container; Yocto owns its caches under `.cache/yocto`.

## CI

CI prebuilds the development image, then invokes the same package-local recipes
for code quality, each discovered Rust package, CAD, and PCB. GitHub Actions owns
only scheduling, caches, artifacts, permissions, and releases.

Firmware configuration is checked with `just firmware-check` and built with
`just firmware`. The full Yocto build is intentionally absent from the everyday
`just check` gate.

The version-controlled Git hook and `.pre-commit-config.yaml` both invoke
`just precommit`, which excludes expensive CAD renders and PCB fabrication
output.
