# Development tools

This directory contains repository maintenance and development tooling. Product
runtime behavior does not belong here.

`check` is the canonical local and CI quality gate.

`cad` and `electronics` are the two hardware entry points. They are deliberately
identical: both source `lib/pipeline.sh`, which owns project discovery,
`generation-order` sorting and command dispatch, so each runner only supplies
the parts that genuinely differ — its toolchain, how one generator is executed,
and its own checks.

Both accept the same commands:

| Command | Effect |
|---|---|
| `list` | Show project generators in dependency order |
| `setup` | Install the toolchain only, without generating |
| `build` | Run every project generator |
| `generate` | Same as `build` |
| `check` | Run that domain's checks |
| `help` | Show usage |

Each domain writes all of its output to `hardware/<domain>/generated`, and
`build` clears that folder first so a removed project cannot leave a stale
artefact behind.

The toolchains install into the ignored `.cache` directory rather than onto the
host: `electronics` creates a virtual environment and installs
`hardware/electronics/requirements.txt`, and `cad` downloads a checksum-verified
Blender build unless `BLENDER_BIN` points at an existing one.
