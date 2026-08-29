# Development

## Purpose

Describe the supported repository workflow.

## Development container

Open the repository in VS Code or Cursor and run **Dev Containers: Reopen in
Container**. See
[`.devcontainer/README.md`](../.devcontainer/README.md).

The image provides:

- stable Rust with `rustfmt` and Clippy;
- Python 3, pip, and venv for CAD dimension checks and Schemdraw schematics;
- the `thumbv8m.main-none-eabihf` compilation target;
- native build, USB, and udev development libraries;
- Rust, Python, TOML, LLDB, Markdown, and GitHub Actions editor integration.

Container creation configures the repository's pre-commit hook and runs the
quality checks automatically. The portable configuration does not expose host
USB devices or install a flashing utility; those choices depend on the
firmware tooling and host operating system.

## Electronics schematics

Python plus [Schemdraw](https://schemdraw.readthedocs.io/en/stable/) is enough.
From the repository root:

```sh
./tools/electronics list
./tools/electronics build
./tools/electronics generate
./tools/electronics check
```

`list` shows project generators in dependency order, the same way
`./tools/generate-cad --list` does for Blender. Adding a schematic is adding a
directory under `hardware/electronics/projects/` with `generate.py`; the runner
discovers it. Adding a component is adding one module to
`hardware/electronics/components/`.

`generate` writes one SVG and PNG per project to the top of
`hardware/electronics/`, then counts the placed symbols into
`hardware/electronics/bom.md`, which lists how many of each part the design
needs. `ELECTRONICS_PNG_DPI` changes the screenshot resolution from its 150 DPI
default.

The first run creates `.cache/electronics` and pip-installs
`hardware/electronics/requirements.txt`.

## Host workflow

Enable the version-controlled pre-commit hook when developing outside the
container:

```sh
git config --local core.hooksPath .githooks
```

Run the complete quality gate directly with:

```sh
./tools/check
```

The gate checks host and firmware formatting, validates and tests the generated
CAD and electronics schematic, type-checks all host workspace targets, runs Clippy
with warnings denied, and runs all host tests. The firmware application at
`apps/firmware` is an independent embedded project, so embedded type-checking
remains deferred until its runtime and linker setup exist.

The pre-commit hook and GitHub **CI** workflow both invoke this same gate.
