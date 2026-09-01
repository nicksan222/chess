# Git hooks

This directory owns version-controlled Git hooks. The pre-commit hook runs
`./tools/check` with CAD generation skipped so commits stay fast; Blender
renders stay on `./tools/cad` and CI. Ruff also runs there via `./tools/python`,
and `.pre-commit-config.yaml` is the same check for `pre-commit run`.
