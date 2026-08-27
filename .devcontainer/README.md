# Development container

This directory owns the reproducible VS Code development environment. It
provides the host Rust toolchain, the embedded compilation target, editor
integration, native build prerequisites, and setup-time repository checks.

Host-specific device access and hardware flashing policy do not belong in the
portable baseline container configuration.
