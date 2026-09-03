# Git hooks

This directory owns version-controlled Git hooks. The pre-commit hook runs
`just precommit`, which composes package-owned recipes while skipping CAD
renders and PCB fabrication output. `.pre-commit-config.yaml` invokes the same
gate for `pre-commit run`.
