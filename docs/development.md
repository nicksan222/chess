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
- Gerbonara in `/opt/pcb`;
- a checksum-verified Blender at `/opt/blender`;
- X11/GL/EGL, Mesa, Xvfb, and `xauth` so headless Blender can render;
- native build, USB, and udev development libraries;
- rust-src, Pylance, YAML, ShellCheck, Docker, Cargo.toml, TOML, LLDB,
  Markdown, and GitHub Actions editor integration.

Container creation configures the repository's pre-commit hook. The image
already contains the hardware toolchains, so the first `./tools/cad` or
`./tools/electronics` inside the container does not download them.

There is no embedded compilation target, because there is no firmware. The board
carries no microcontroller: a Raspberry Pi Zero 2 W reads the sensors and drives
the LEDs directly, so the whole product is one ordinary Linux binary. See
[`architecture.md`](architecture.md) for why.

## Hardware pipelines

`hardware/cad`, `hardware/electronics` and `hardware/pcb` are the same shape, and
their runners do the same sequential job with no subcommands:

```sh
./tools/<domain>           # install if needed, test, then generate
```

Extra arguments are an error. Each script sources `tools/lib/pipeline.sh` only so
generate can list projects in `generation-order`.

Each domain keeps its source in `core/`, `projects/` and `tests/`, and writes
everything it produces to `generated/`. Electronics adds a `components/` catalog
of single parts and PCB adds a `footprints/` catalog; CAD and electronics both
have `blocks/` for reusable composition. Adding a project is adding a directory
under `projects/` with a `generate.py`; adding a component or a footprint is
adding one module. None of it requires editing a runner.

What each writes:

- **CAD** — `<project>.blend` plus one PNG per view.
- **Electronics** — `<project>.svg` and `<project>.png`, then `bom.md` counted
  from the placed symbols, then `netlist.json`. `ELECTRONICS_PNG_DPI` changes the
  screenshot resolution from its 150 DPI default.
- **PCB** — a Gerber and Excellon layer stack, SVG previews of both sides,
  `routing.md`, and a fabrication zip **only when every net is routed**.

### Order matters between two of them

Electronics has to run before PCB. The schematic publishes `netlist.json`, and
the layout reads it rather than importing the schematic, which keeps Schemdraw
out of the fabrication toolchain and makes the contract between the two domains
a file you can read. `./tools/check` and `make gen` both run them in that order.

The toolchains ship in the development container (`/opt/blender`,
`/opt/electronics`, `/opt/pcb`). Outside it they install into the ignored
`.cache` directory: virtual environments for Schemdraw and Gerbonara, and a
checksum-verified Blender build unless `BLENDER_BIN` already points at one.

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
electronics jobs, sequentially. One workspace covers all the Rust in the
repository; there is no separate embedded project to check.

The pre-commit hook runs this gate without CAD generation so commits do not
wait on Blender. GitHub
**CI** prebuilds the development container, then runs `./tools/cad`,
`./tools/electronics`, and `./tools/rust` in parallel through the Dev
Container CLI so later workflows reuse the image instead of downloading
Blender and Python packages on every job.

```sh
devcontainer up --workspace-folder .
devcontainer exec --workspace-folder . ./tools/check
```
