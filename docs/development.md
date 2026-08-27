# Development

## Purpose

Describe the supported repository workflow.

## Development container

Open the repository in VS Code and run **Dev Containers: Reopen in Container**.
The image provides:

- stable Rust with `rustfmt` and Clippy;
- the `thumbv8m.main-none-eabihf` compilation target;
- native build, USB, and udev development libraries;
- Rust, TOML, LLDB, Markdown, and GitHub Actions editor integration.

Container creation runs the host workspace checks automatically. The portable
configuration does not expose host USB devices or install a flashing utility;
those choices depend on the firmware tooling and host operating system.

## Host workflow

The root Cargo workspace contains host-side crates, apps, and `xtask`. Run:

```sh
cargo fmt --check
cargo check --workspace
cargo test --workspace
```

The firmware application at `apps/firmware` is an independent embedded project
and is not part of these checks.

GitHub Actions runs the same commands in the **CI** workflow.
