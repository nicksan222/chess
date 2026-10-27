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

# Check diff success before classification; process substitution hides its status.
changes=$(mktemp)
trap 'rm -f "$changes"' EXIT
git diff --name-only -z "$base...$head" > "$changes"

while IFS= read -r -d '' file; do
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
    # Python lint and pytest policy needs both domain test pipelines.
    pyproject.toml)
        pcb=true
        cad=true
        ;;
    # Quality job only: repository lint rules and their tools, and the Git hook.
    tooling/* | sgconfig.yml | typos.toml | .editorconfig | \
        .editorconfig-checker.json | .githooks/*)
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
done < "$changes"

hardware=false
if [[ "$pcb" == true || "$cad" == true ]]; then hardware=true; fi

echo "pcb=$pcb"
echo "cad=$cad"
echo "hardware=$hardware"
echo "rust=$rust"
echo "quality=$quality"
