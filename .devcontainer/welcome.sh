#!/usr/bin/env bash
# On-demand overview of the development toolchain.
set -uo pipefail

tool() {
    local name=$1 binary=$2 version
    shift 2
    if command -v "${binary}" >/dev/null 2>&1; then
        version=$("$@" 2>/dev/null | head -n 1)
        printf '  %-18s %s\n' "${name}" "${version:-installed}"
    else
        printf '  %-18s missing\n' "${name}"
    fi
}

printf 'Chess development tools\n'
tool Rust cargo cargo --version
tool Just just just --version
tool Python python3 python3 --version
tool Ruff ruff ruff --version
tool cargo-deny cargo-deny cargo-deny --version
tool cargo-shear cargo-shear cargo-shear --version
tool ast-grep ast-grep ast-grep --version
tool actionlint actionlint actionlint --version
tool typos typos typos --version
tool editorconfig-checker editorconfig-checker editorconfig-checker --version
tool KiCad kicad-cli kicad-cli version
tool Blender "${BLENDER_BIN:-blender}" "${BLENDER_BIN:-blender}" --version
tool Docker docker docker --version
printf '\nRun just --list for recipes; see docs/development.md for workflows.\n'
