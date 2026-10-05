#!/usr/bin/env bash
set -euo pipefail

git config --local core.hooksPath .githooks

# Docker creates new named volumes as root; each agent runtime must persist state.
sudo chown "$(id -u):$(id -g)" \
    "${HOME}/.pi/agent" "${HOME}/.local/share/pi-worktrees" \
    "${HOME}/.claude" "${HOME}/.codex" "${HOME}/.config/herdr"
# Node comes from a devcontainer feature, so npm harnesses install here, pinned.
# Claude Code and Herdr are pinned in the image (see Dockerfile).
npm install --global --ignore-scripts \
    @earendil-works/pi-coding-agent@1.0.3 @openai/codex@0.159.3
for harness in pi claude codex herdr; do
    if ! command -v "${harness}" >/dev/null 2>&1; then
        printf 'error: agent harness %s is not installed; rebuild the container\n' \
            "${harness}" >&2
        exit 1
    fi
done
bun install --cwd .pi --frozen-lockfile
bun run --cwd .pi check

if ! command -v python3 >/dev/null 2>&1; then
    printf 'error: python3 is required in the development container\n' >&2
    exit 1
fi

python3 .agents/team/setup.py
python3 .agents/team/agents.py list

cat <<'EOF'

The container is ready. Hardware toolchains, Bun, Pi, Claude Code, Codex and Herdr are installed.

  bun run --cwd .pi check     type-check project Pi extensions
  pi                          start the Pi coding agent
  claude auth login           sign in to Claude (persisted across rebuilds)
  just agents-doctor          check Herdr tools/login without model requests
  just agents lead developer  start a small team (asks Claude Code or Pi)
  just agents                 start the eight-role engineering team
  just agents --harness pi    start the team in Pi without asking
  just agents lead hardware-engineer mechanical-engineer  circuit/enclosure team
  just                        list repository capabilities
  just cad                    test, then generate CAD output
  just pcb                    test, then generate PCB review output
  just quality                lint and format-check every package
  just firmware-binary        link the firmware for AArch64
  just check                  all domains, sequentially
EOF
