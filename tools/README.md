# Development tools

This directory contains repository maintenance and development tooling. Product
runtime behavior does not belong here.

`check` is the canonical local and CI quality gate.
`generate-cad` is the local entry point used by `make regen-all` to regenerate
Blender projects and inspection renders. It discovers generators dynamically and
uses optional per-project `generation-order` files for dependencies.
`electronics` is the single electronics entry point, parallel to
`generate-cad`. `list` shows discovered project `generate.py` files. `build`
and `generate` run them, write one SVG and PNG per project to the top of
`hardware/electronics/`, and rebuild `hardware/electronics/bom.md`. `check`
builds, then runs the electronics tests. The first run creates
`.cache/electronics` and installs Schemdraw from
`hardware/electronics/requirements.txt`.
