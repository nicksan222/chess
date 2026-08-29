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
- Schemdraw and matplotlib in `/opt/electronics`;
- a checksum-verified Blender at `/opt/blender`;
- X11/GL/EGL, Mesa, Xvfb, and `xauth` so headless Blender can render;
- the `thumbv8m.main-none-eabihf` compilation target;
- native build, USB, and udev development libraries;
- Rust, Python, TOML, LLDB, Markdown, and GitHub Actions editor integration.

Container creation configures the repository's pre-commit hook. The image
already contains the hardware toolchains, so the first `./tools/cad` or
`./tools/electronics` inside the container does not download them.
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

The toolchains ship in the development container (`/opt/blender`,
`/opt/electronics`). Outside it they install into the ignored `.cache`
directory: a virtual environment for Schemdraw, and a checksum-verified Blender
build unless `BLENDER_BIN` already points at one.

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

The gate runs `./tools/rust` (format, Clippy, tests), then the full CAD and
electronics jobs, sequentially. The firmware application at `apps/firmware` is
an independent embedded project, so embedded type-checking remains deferred
until its runtime and linker setup exist.

The pre-commit hook invokes this same gate on the developer machine. GitHub
**CI** prebuilds the development container, then runs `./tools/cad`,
`./tools/electronics`, and `./tools/rust` in parallel through the Dev
Container CLI so later workflows reuse the image instead of downloading
Blender and Python packages on every job.

```sh
devcontainer up --workspace-folder .
devcontainer exec --workspace-folder . ./tools/check
```
