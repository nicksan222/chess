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

Container creation configures the repository's pre-commit hook and runs the
quality checks automatically. The portable configuration does not expose host
USB devices or install a flashing utility; those choices depend on the firmware
tooling and host operating system.

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

The gate checks host and firmware formatting, type-checks all host workspace
targets, runs Clippy with warnings denied, and runs all host tests. The firmware
application at `apps/firmware` is an independent embedded project, so embedded
type-checking remains deferred until its runtime and linker setup exist.

The pre-commit hook and GitHub **CI** workflow both invoke this same gate.
