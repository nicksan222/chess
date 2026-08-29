# Development tools

This directory contains repository maintenance and development tooling. Product
runtime behavior does not belong here.

`check` is the canonical local and CI quality gate. It runs `cad` and
`electronics` in full — not a subset.

`cad` and `electronics` are the two hardware entry points. Each script is one
sequential job with no subcommands:

1. Install the toolchain if it is not already there.
2. Run that domain's tests.
3. Run every project generator into `hardware/<domain>/generated/`.

```sh
./tools/cad
./tools/electronics
```

Extra arguments are an error. Both scripts source `lib/pipeline.sh` only so
generate can walk `projects/*/generate.py` in `generation-order`.

Each domain writes all of its output to `hardware/<domain>/generated`, and
generate clears that folder first so a removed project cannot leave a stale
artefact behind.

The toolchains install into the ignored `.cache` directory rather than onto the
host: `electronics` creates a virtual environment and installs
`hardware/electronics/requirements.txt`, and `cad` downloads a checksum-verified
Blender build unless `BLENDER_BIN` points at an existing one.

CI runs those scripts the same way a developer does, through the Dev Container
CLI, so the Dockerfile is the only place runtime packages are declared.
