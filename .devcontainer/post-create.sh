#!/usr/bin/env bash
set -euo pipefail

git config --local core.hooksPath .githooks

if ! command -v python3 >/dev/null 2>&1; then
    printf 'error: python3 is required in the development container\n' >&2
    exit 1
fi

# Prepare both hardware toolchains up front so the first build is not also the
# first download: Schemdraw into .cache/electronics, Blender into .cache/blender.
./tools/electronics setup
./tools/cad setup

cat <<'EOF'

The container is ready. Both hardware toolchains are installed under .cache.

  ./tools/electronics         install if needed, test, then generate
  ./tools/cad                 install if needed, test, then generate
  make check                  the full gate, including the Rust workspace
EOF
