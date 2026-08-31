# Development container

This directory owns the reproducible VS Code / Cursor development environment.
The Dockerfile installs every toolchain the jobs need: Blender, Gerbonara, and
the Rust components. Open the repository and run **Dev Containers:
Reopen in Container**, or drive it from the
[`devcontainer` CLI](https://github.com/devcontainers/cli):

```sh
devcontainer up --workspace-folder .
devcontainer exec --workspace-folder . ./tools/pcb
devcontainer exec --workspace-folder . ./tools/cad
devcontainer exec --workspace-folder . ./tools/rust
devcontainer exec --workspace-folder . make check
```

The image provides:

- stable Rust with `rustfmt` and Clippy;
- Gerbonara in `/opt/pcb`;
- a checksum-verified Blender at `/opt/blender`;
- X11/GL/EGL, Mesa, Xvfb, and `xauth` so headless Blender can render;
- native build, USB, and udev development libraries;
- rust-src, Pylance, YAML, ShellCheck, Docker, Cargo.toml, TOML, LLDB,
  Markdown, and GitHub Actions editor integration.

CI prebuilds this image, pushes it to GHCR, then runs CAD, PCB, and Rust as
parallel `devcontainer exec` jobs against that digest. Subsequent
prebuilds reuse the image layers when the Dockerfile is unchanged.

Container creation configures the repository pre-commit hook. Host-only
fallback downloads (`.cache/blender`, `.cache/pcb`) exist for people
who run the tools outside the container.

After create:

```sh
./tools/pcb                 # test, then generate
./tools/cad                 # test, then generate
./tools/rust                # fmt, clippy, and tests
make check                  # all three, sequentially
```

Host-specific device access and hardware flashing policy do not belong in the
portable baseline container configuration.
