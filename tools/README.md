# Repository tools

Run commands from the repository root:

- `./tools/check` — complete repository validation.
- `./tools/quality` — all repository code-quality checks.
- `./tools/python` — lint and format-check CAD, PCB, and shared Python with Ruff.
- `./tools/rust` — format, check, lint, test, and document Rust.
- `./tools/shared-hardware` — validate shared dimensions, wiring, and mappings.
- `./tools/cad` — validate, test, and generate Blender models and renders.
- `./tools/pcb` — validate, test, and generate PCB fabrication output.

CAD and PCB runners install ignored local toolchains when container-provided ones
are unavailable. The PCB connectivity and BOM are reviewed sources under
`hardware/pcb/design`; there is no separate schematic-generation step.
