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

The PCB's reviewed sources are `hardware/pcb/board/data/netlist.json` and the
component catalog. Generation validates them against every footprint and copper
connection, then writes the BOM under `hardware/pcb/generated/`. CAD and PCB
both consume `hardware/shared`, preventing the mechanical and electrical layouts
from independently copying dimensions or mappings.

Generated hardware artifacts remain under each domain's `generated/` directory.
When host connectivity changes, `just --justfile hardware/pcb/justfile pins`
regenerates the board and writes `apps/firmware/src/generated_pins.rs`; the
separate `pins-check` recipe rejects stale output without rewriting it. The CAD
recipe creates an ignored fallback toolchain under `.cache/blender` outside the
container; Yocto owns its caches under `.cache/yocto`.

## CI

The `PR` workflow invokes package-local recipes for code quality, every Rust
package, CAD, PCB, and firmware, and runs the Bun-managed `.pi` typecheck and
test suite with its frozen lockfile. In addition to host tests and Yocto metadata
validation, `Firmware checks / AArch64 binary` performs a locked optimized build
and links the real firmware executable for the Pi architecture. Cargo follows the
firmware package's complete dependency graph automatically, including local
workspace crates, target-specific code, build scripts, and native linkage. The
resulting executable is retained as a seven-day workflow artifact. This takes a
small fraction of a Linux image build and runs alongside CAD and PCB. Branch
protection requires the `Required checks` job on this workflow.

Push `CI` on `main` runs the same Hardware, Quality, and Pi harness jobs without
the pull-request firmware checks. Full Yocto image builds are isolated in the
`Firmware` workflow. Every successful `main` CI run starts it as a sibling
workflow after the normal checks, and it also runs weekly to detect ecosystem
drift or manually against any selected branch with **Actions → Firmware → Run
workflow**. A `v*` tag calls the same build only after the complete tag CI graph
succeeds, and only that gated invocation may publish release assets. Locally,
`just firmware-check` parses and dry-runs the BitBake image graph,
`just firmware-binary` builds the AArch64 application, and `just firmware`
constructs the complete image.

The version-controlled Git hook and `.pre-commit-config.yaml` both invoke
`just precommit`, which excludes expensive CAD renders and PCB fabrication
output.
