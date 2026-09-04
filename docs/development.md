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

Pull request CI invokes package-local recipes for code quality, every Rust
package, CAD, PCB, and firmware. Firmware metadata checks run immediately. When
a PR changes firmware, its Rust dependencies, the build configuration, or the
toolchain, a parallel `Firmware plan` parses the complete BitBake configuration
and dry-runs the exact `firmware-image` task graph without compiling it. For
unrelated PRs the plan reuses the validated base assumption and finishes
immediately. The stable `Required checks` job fails unless every applicable job
succeeds.

Full Yocto image builds are isolated in the reusable `Firmware` workflow. They
run weekly to detect ecosystem drift or manually against any selected branch
with **Actions → Firmware → Run workflow**. A `v*` tag calls the same build only
after the complete tag CI graph succeeds, and only that gated invocation may
publish release assets. Locally, `just firmware-check` performs the parse and
dry-run, while `just firmware` builds the complete image.

The version-controlled Git hook and `.pre-commit-config.yaml` both invoke
`just precommit`, which excludes expensive CAD renders and PCB fabrication
output.
