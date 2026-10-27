# Development container

This directory owns the reproducible VS Code / Cursor development environment.
Open the repository and run **Dev Containers: Reopen in Container**, or use the
[`devcontainer` CLI](https://github.com/devcontainers/cli):

```sh
devcontainer up --workspace-folder .
devcontainer exec --workspace-folder . just --list
```

The image provides:

- pinned Rust with `rustfmt`, Clippy, Just, and the AArch64 GNU target/linker;
- Ruff for CAD, PCB, and shared Python;
- pinned quality and dependency tools including ast-grep, cargo-deny,
  cargo-shear and pip-audit (see `tooling/quality/README.md`);
- KiCad 9 with `kicad-cli` and `pcbnew`, and checksum-verified Blender;
- X11/GL/EGL, Mesa, Xvfb, and `xauth` for headless Blender rendering;
- an in-container Docker daemon for Yocto metadata validation, plus native build,
  USB, and udev development libraries;
- Rust, Python, YAML, ShellCheck, Docker, TOML, LLDB, Markdown, and GitHub
  Actions editor integration.

CI prebuilds this image and runs Hardware and Quality against that digest.
Hardware checks shared contracts, PCB and CAD sequentially; Rust quality and
tests share a separate container. See the [workflow guide](../.github/workflows/README.md).
Container creation configures the repository pre-commit hook. Run `just welcome` for an on-demand tool overview;
see [`docs/development.md`](../docs/development.md) for workflows and commands.

Coding agents are optional. Install and configure your preferred agent yourself
outside the baseline container setup; shared project instructions are in
[`.agents/README.md`](../.agents/README.md).

Host-specific device access and hardware flashing policy do not belong in the
portable baseline container configuration.
