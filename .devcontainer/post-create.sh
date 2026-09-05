#!/usr/bin/env bash
set -euo pipefail

git config --local core.hooksPath .githooks

# Docker creates new named volumes as root; Pi must be able to persist state.
sudo chown "$(id -u):$(id -g)" "${HOME}/.pi/agent" "${HOME}/.local/share/pi-worktrees"
npm install --global --ignore-scripts @earendil-works/pi-coding-agent
bun install --cwd .pi --frozen-lockfile
bun run --cwd .pi check

if ! command -v python3 >/dev/null 2>&1; then
    printf 'error: python3 is required in the development container\n' >&2
    exit 1
fi

cat <<'EOF'

The container is ready. Hardware toolchains, Bun, and Pi are installed.

  bun run --cwd .pi check     type-check project Pi extensions
  pi                          start the Pi coding agent
  just                        list repository capabilities
  just cad                    test, then generate CAD output
  just pcb                    test, then generate PCB review output
  just quality                lint and format-check every package
  just firmware-binary        link the firmware for AArch64
  just check                  all domains, sequentially
EOF
