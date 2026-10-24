#!/usr/bin/env bash
# Classify the files a pull request changes into CI scopes and write
# `hardware=<bool>`, `rust=<bool>` and `quality=<bool>` lines to stdout
# (GITHUB_OUTPUT format).
#
# Usage: changed-scopes.sh <base-sha> <head-sha>
#
# Files are diffed from the merge base (`base...head`), so commits that landed
# on the base branch after the pull request branched never count as its
# changes. Unknown paths enable every scope, so a new top-level directory can
# never silently skip a check. Only paths known to be inert (documentation and
# repository metadata) skip everything.
set -euo pipefail

base="$1"
head="$2"
hardware=false
rust=false
quality=false

while IFS= read -r file; do
    case "$file" in
    # Inert: prose and repository metadata that no job reads.
    *.md | docs/* | LICENSE | .github/CODEOWNERS | .github/ISSUE_TEMPLATE/* | \
        .agents/* | .claude/* | .codex/*) ;;
    # Rust workspace and its lint and dependency policy only.
    apps/* | crates/* | Cargo.toml | Cargo.lock | rust-toolchain.toml | \
        clippy.toml | deny.toml)
        rust=true
        ;;
    # Hardware generation only: no Rust code reads hardware/, and pyproject.toml
    # configures the hardware Python lint and tests.
    hardware/* | pyproject.toml)
        hardware=true
        ;;
    # Quality job only: repository lint rules, their tools and the Git hook.
    tooling/* | sgconfig.yml | .ls-lint.yml | typos.toml | .editorconfig | \
        .editorconfig-checker.json | .githooks/*)
        quality=true
        ;;
    # Everything else (workflows, the dev container, the root justfile, unknown paths).
    *)
        hardware=true
        rust=true
        quality=true
        ;;
    esac
done < <(git diff --name-only "$base...$head")

echo "hardware=$hardware"
echo "rust=$rust"
echo "quality=$quality"
