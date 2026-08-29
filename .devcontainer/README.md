# Development container

This directory owns the reproducible VS Code / Cursor development environment.
Open the repository and run **Dev Containers: Reopen in Container**, or drive it
from the [`devcontainer` CLI](https://github.com/devcontainers/cli):

```sh
devcontainer up --workspace-folder .
devcontainer exec --workspace-folder . ./tools/electronics
devcontainer exec --workspace-folder . ./tools/cad
devcontainer exec --workspace-folder . make check
```

The image provides:

- stable Rust with `rustfmt` and Clippy;
- Python 3, pip, and venv for Schemdraw schematics and CAD dimension checks;
- `curl`, `xz-utils`, X11/GL/EGL, Mesa, and Xvfb so headless Blender can
  render, and `./tools/cad` needs nothing from the host;
- the `thumbv8m.main-none-eabihf` compilation target;
- native build, USB, and udev development libraries;
- Rust, Python, TOML, LLDB, Markdown, and GitHub Actions editor integration.

Container creation configures the repository pre-commit hook. The first
`./tools/electronics` or `./tools/cad` installs that domain's toolchain into
`.cache/electronics` or `.cache/blender`. Both live in the workspace, so they
survive a rebuild and never touch the host.

After create:

```sh
./tools/electronics         # install if needed, test, then generate
./tools/cad                 # install if needed, test, then generate
make check                  # the full gate, including the Rust workspace
```

Host-specific device access and hardware flashing policy do not belong in the
portable baseline container configuration.
