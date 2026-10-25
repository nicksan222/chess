#!/usr/bin/env bash
# Classify the files a pull request changes into CI scopes and write
# `pcb=<bool>`, `cad=<bool>`, `hardware=<bool>` (either of them), `rust=<bool>`
# and `quality=<bool>` lines to stdout (GITHUB_OUTPUT format).
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
pcb=false
cad=false
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
    # Hardware generation; no Rust code reads hardware/. The PCB review decides
    # whether its regenerated export changed enough to need CAD as well.
    hardware/pcb/*)
        pcb=true
        ;;
    # CAD only: it reuses the checked-in PCB export.
    hardware/cad/*)
        cad=true
        ;;
    # Shared physical and electrical contracts feed both generators.
    hardware/shared/*)
        pcb=true
        cad=true
        ;;
    # Quality job only: repository lint rules and their tools, the Git hook, and
    # pyproject.toml (Ruff and pytest settings change no generated artifact; the
    # Quality job runs Ruff, basedpyright and the PCB checks with board tests).
    tooling/* | sgconfig.yml | .ls-lint.yml | typos.toml | .editorconfig | \
        .editorconfig-checker.json | .githooks/* | pyproject.toml)
        quality=true
        ;;
    # Everything else (workflows, the dev container, the root justfile, unknown paths).
    *)
        pcb=true
        cad=true
        rust=true
        quality=true
        ;;
    esac
done < <(git diff --name-only "$base...$head")

hardware=false
if [[ "$pcb" == true || "$cad" == true ]]; then hardware=true; fi

echo "pcb=$pcb"
echo "cad=$cad"
echo "hardware=$hardware"
echo "rust=$rust"
echo "quality=$quality"
