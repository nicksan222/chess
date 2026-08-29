# Development

## Purpose

Describe the supported repository workflow.

## Development container

Open the repository in VS Code or Cursor and run **Dev Containers: Reopen in
Container**, or use the
[`devcontainer` CLI](https://github.com/devcontainers/cli):

```sh
devcontainer up --workspace-folder .
devcontainer exec --workspace-folder . ./tools/electronics
devcontainer exec --workspace-folder . ./tools/cad
devcontainer exec --workspace-folder . make check
```

See [`.devcontainer/README.md`](../.devcontainer/README.md).

The image provides:

- stable Rust with `rustfmt` and Clippy;
- Python 3, pip, and venv for CAD dimension checks and Schemdraw schematics;
- `curl`, `xz-utils`, X11/GL/EGL, Mesa, and Xvfb so headless Blender can
  render;
- the `thumbv8m.main-none-eabihf` compilation target;
- native build, USB, and udev development libraries;
- Rust, Python, TOML, LLDB, Markdown, and GitHub Actions editor integration.

Container creation configures the repository's pre-commit hook. The first
`./tools/electronics` or `./tools/cad` installs that domain's toolchain into
`.cache`. Creation deliberately stops there rather than running the full gate;
`make check` is one command away.
The portable configuration does not expose host USB devices or install a
flashing utility; those choices depend on the firmware tooling and host
operating system.

## Hardware pipelines

`hardware/cad` and `hardware/electronics` are the same shape, and
`./tools/cad` and `./tools/electronics` do the same sequential job with no
subcommands:

```sh
./tools/<domain>           # install if needed, test, then generate
```

Extra arguments are an error. Both scripts source `tools/lib/pipeline.sh` only
so generate can list projects in `generation-order`.

Each domain keeps its source in `core/`, `blocks/`, `projects/` and `tests/`,
and writes everything it produces to `generated/`. Electronics additionally has
a `components/` catalog of single parts. Adding a project is adding a directory
under `projects/` with a `generate.py`; adding an electronics component is
adding one module to `components/`. Neither requires editing a runner.

CAD writes `<project>.blend` plus one PNG per view. Electronics writes
`<project>.svg` and `<project>.png`, then counts the placed symbols into
`bom.md`, which lists how many of each part the design needs.
`ELECTRONICS_PNG_DPI` changes the screenshot resolution from its 150 DPI
default.

The toolchains install into the ignored `.cache` directory: a virtual
environment for Schemdraw, and a checksum-verified Blender build unless
`BLENDER_BIN` points at an existing one.

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

The gate checks host and firmware formatting, runs the full CAD and electronics
jobs (install if needed, test, generate), type-checks all host workspace
targets, runs Clippy with warnings denied, and runs all host tests. The firmware
application at
`apps/firmware` is an independent embedded project, so embedded type-checking
remains deferred until its runtime and linker setup exist.

The pre-commit hook invokes this same gate on the developer machine. GitHub
**CI** does not install a second copy of those dependencies: it runs the
Dev Container CLI against this repository, then the same gate inside that
container.

```sh
devcontainer up --workspace-folder .
devcontainer exec --workspace-folder . ./tools/check
```

The workflow caches the built image on GHCR and the workspace `.cache` and
`target` directories so later runs skip the Blender download, Python venv,
image rebuild, and Rust crate rebuilds.
