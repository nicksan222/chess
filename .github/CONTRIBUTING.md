# Contributing

Thanks for helping build Chess. Contributions to firmware, software, electronics,
mechanical design, documentation, and testing are welcome.

## Before starting

- Search existing issues and pull requests before opening a duplicate.
- Open an issue before undertaking a large design or architecture change.
- Keep pull requests focused; unrelated changes are easier to review separately.
- Do not present generated hardware output as physically validated evidence.

## Development

Use the [development guide](../docs/development.md) for setup and validation
commands, and `just --list` to discover recipes. Each application, crate and
hardware domain owns its local `justfile`.

## Pull requests

1. Create a branch from `main`.
2. Add tests for behavior changes.
3. Update documentation when interfaces, hardware, or workflows change.
4. Run the relevant package recipe and `just precommit`.
5. Describe the motivation, validation, and any physical assumptions in the PR.

By contributing, you agree that your contribution is licensed under the
repository's [MIT License](../LICENSE).
