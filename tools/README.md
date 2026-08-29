# Development tools

This directory contains repository maintenance and development tooling. Product
runtime behavior does not belong here.

`check` is the canonical local quality gate. It runs `rust`, `cad`, and
`electronics` in full — not a subset.

`cad` and `electronics` are the two hardware entry points. Each script is one
sequential job with no subcommands:

1. Use the toolchain if it is already there (the development image, `BLENDER_BIN`,
   or `.cache`).
2. Run that domain's tests.
3. Run every project generator into `hardware/<domain>/generated/`.

`rust` is the Cargo gate: format, type-check, Clippy, and tests.

```sh
./tools/cad
./tools/electronics
./tools/rust
```

Extra arguments are an error. The hardware scripts source `lib/pipeline.sh` only
so generate can walk `projects/*/generate.py` in `generation-order`.

Each hardware domain writes all of its output to `hardware/<domain>/generated`,
and generate clears that folder first so a removed project cannot leave a stale
artefact behind.

The development container Dockerfile downloads Blender and the Schemdraw venv
into `/opt`. Host runs fall back to `.cache`. CI prebuilds that image, then
runs the three tools in parallel through the Dev Container CLI.
