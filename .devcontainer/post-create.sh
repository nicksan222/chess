#!/usr/bin/env bash
set -euo pipefail

workspace=$(pwd)
step_number=0
step() {
    step_number=$((step_number + 1))
    printf '\n\e[1m%s  [%d/6] %s\e[0m\n' "$1" "${step_number}" "$2"
}
fail() {
    printf '\n❌ \e[31merror:\e[0m %s\n' "$1" >&2
    exit 1
}
trap 'printf "\n💥 Container setup failed at step %d. Scroll up for details.\n" "${step_number}" >&2' ERR

printf '\n♟️  \e[1mSetting up the Chess development container…\e[0m\n'

step "🪝" "Configuring the repository pre-commit hook"
git config --local core.hooksPath .githooks

step "📦" "Claiming persistent agent volumes"
# Docker creates new named volumes as root; each agent runtime must persist state.
sudo chown "$(id -u):$(id -g)" \
    "${HOME}/.pi/agent" "${HOME}/.local/share/pi-worktrees" \
    "${HOME}/.claude" "${HOME}/.codex" "${HOME}/.config/herdr"

step "🤖" "Installing Pi and Codex"
# Node comes from a devcontainer feature, so npm harnesses install here, pinned.
# Claude Code and Herdr are pinned in the image (see Dockerfile).
npm install --global --ignore-scripts \
    @earendil-works/pi-coding-agent@1.0.3 @openai/codex@0.159.3
for harness in pi claude codex herdr; do
    if ! command -v "${harness}" >/dev/null 2>&1; then
        fail "agent harness ${harness} is not installed; rebuild the container"
    fi
done

step "🥟" "Installing and type-checking Pi extensions"
bun install --cwd .pi --frozen-lockfile
bun run --cwd .pi check

step "👥" "Configuring the Herdr agent team"
if ! command -v python3 >/dev/null 2>&1; then
    fail "python3 is required in the development container"
fi
python3 .agents/team/setup.py
python3 .agents/team/agents.py list

step "👋" "Installing the terminal welcome"
# Show our welcome once, in the first VS Code terminal, instead of the base image notice.
mkdir -p "${HOME}/.config/vscode-dev-containers" "${HOME}/.config/chess"
touch "${HOME}/.config/vscode-dev-containers/first-run-notice-already-displayed"
rm -f "${HOME}/.config/chess/welcome-shown"
if ! grep -q '# chess-welcome' "${HOME}/.bashrc" 2>/dev/null; then
    cat >>"${HOME}/.bashrc" <<EOF

# chess-welcome: show the Chess welcome once after the container is created.
if [ -t 1 ] && [ ! -f "\${HOME}/.config/chess/welcome-shown" ] \\
    && [ -x "${workspace}/.devcontainer/welcome.sh" ]; then
    touch "\${HOME}/.config/chess/welcome-shown"
    "${workspace}/.devcontainer/welcome.sh"
fi
EOF
fi

trap - ERR
printf '\n🎉 \e[1;32mThe container is ready!\e[0m Open a new terminal for the tour, or run \e[36mjust welcome\e[0m.\n'
"${workspace}/.devcontainer/welcome.sh"
