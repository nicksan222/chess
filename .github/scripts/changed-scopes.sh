#!/usr/bin/env bash
# Classify the files changed between two commits into CI scopes and write
# `hardware=<bool>` and `rust=<bool>` lines to stdout (GITHUB_OUTPUT format).
#
# Usage: changed-scopes.sh <base-sha> <head-sha>
#
# Unknown paths enable every scope, so a new top-level directory can never
# silently skip a check. Only paths known to be inert (documentation and
# repository metadata) skip everything.
set -euo pipefail

base="$1"
head="$2"
hardware=false
rust=false

while IFS= read -r file; do
    case "$file" in
    # Inert: prose and repository metadata that no job reads.
    *.md | docs/* | LICENSE | .github/CODEOWNERS | .github/ISSUE_TEMPLATE/* | \
        .agents/* | .claude/* | .codex/* | AGENTS.md | GEMINI.md) ;;
    # Rust workspace only.
    apps/* | crates/* | Cargo.toml | Cargo.lock | rust-toolchain.toml)
        rust=true
        ;;
    # Hardware generation only.
    hardware/cad/* | hardware/pcb/*)
        hardware=true
        ;;
    # Everything else (shared contracts, tooling, workflows, unknown paths).
    *)
        hardware=true
        rust=true
        ;;
    esac
done < <(git diff --name-only "$base" "$head")

echo "hardware=$hardware"
echo "rust=$rust"
