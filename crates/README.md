# Shared crates

This directory contains reusable Rust libraries. Shared crates remain independent
of executable applications and adapter implementations.

cargo-deny enforces this from the dependency graph
(`just --justfile tooling/quality/justfile boundaries`): no crate here reaches
`firmware`, `tokio`, `gpiocdev` or `nmrs`, even through dev-dependencies
(`tooling/quality/portable.deny.toml`), and workspace crates depend on each
other only as the `wrappers` in the root `deny.toml` list. A new crate or
internal dependency starts by updating those lists.
