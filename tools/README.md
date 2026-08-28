# Development tools

This directory contains repository maintenance and development tooling. Product
runtime behavior does not belong here.

`check` is the canonical local and CI quality gate.
`generate-cad` is the local entry point used by `make regen-all` to regenerate
Blender projects and inspection renders. It discovers generators dynamically and
uses optional per-project `generation-order` files for dependencies.
