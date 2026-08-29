# Development tools

This directory contains repository maintenance and development tooling. Product
runtime behavior does not belong here.

`check` is the canonical local and CI quality gate.

`cad` and `electronics` are the two hardware entry points. Invoking either
with no arguments does the full job, in order:

1. Install the toolchain if it is not already there.
2. Run that domain's tests.
3. Run every project generator.

```sh
./tools/cad
./tools/electronics
```

Optional commands stay available when you only want one of those steps:

| Command | Effect |
|---|---|
| `list` | Show project generators in dependency order |
| `setup` | Install the toolchain only |
| `check` | Setup, then run tests |
| `build` | Setup, then generate |
| `help` | Show usage |

Both scripts source `lib/pipeline.sh` only to list `projects/*/generate.py`
in `generation-order`. Setup, tests and generate stay in the runner so each
file reads top to bottom.

Each domain writes all of its output to `hardware/<domain>/generated`, and
generate clears that folder first so a removed project cannot leave a stale
artefact behind.

The toolchains install into the ignored `.cache` directory rather than onto the
host: `electronics` creates a virtual environment and installs
`hardware/electronics/requirements.txt`, and `cad` downloads a checksum-verified
Blender build unless `BLENDER_BIN` points at an existing one.
