#!/usr/bin/env bash
set -euo pipefail

git config --local core.hooksPath .githooks

if ! command -v python3 >/dev/null 2>&1; then
    printf 'error: python3 is required in the development container\n' >&2
    exit 1
fi

cat <<'EOF'

The container is ready. Hardware toolchains are already in the image.

  ./tools/cad                 test, then generate
  ./tools/pcb                 test, then generate fabrication output
  ./tools/python              lint and format-check hardware Python
  ./tools/rust                fmt, clippy, and tests
  make check                  all domains, sequentially
EOF
