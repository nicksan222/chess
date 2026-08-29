# Development container

This directory owns the reproducible VS Code / Cursor development environment.
Open the repository and run **Dev Containers: Reopen in Container**.

The image provides:

- stable Rust with `rustfmt` and Clippy;
- Python 3, pip, and venv for CAD dimension checks and Schemdraw schematics;
- the `thumbv8m.main-none-eabihf` compilation target;
- native build, USB, and udev development libraries;
- Rust, Python, TOML, LLDB, Markdown, and GitHub Actions editor integration.

Container creation configures the repository pre-commit hook and runs
`./tools/check`.

After create:

```sh
make electronics         # rewrite schematic SVG and PNG
make electronics-check   # generate drawings and run topology tests
make gen                 # CAD (downloads Blender on first use) + electronics
```

Host-specific device access and hardware flashing policy do not belong in the
portable baseline container configuration.
