#!/usr/bin/env bash
# Friendly devcontainer welcome: toolchain/login status and the commands that matter.
# Read-only: it never starts a model, signs in, or changes the workspace.
set -uo pipefail

if [[ -t 1 && -z "${NO_COLOR:-}" ]]; then
    bold=$'\e[1m' dim=$'\e[2m' green=$'\e[32m' yellow=$'\e[33m' cyan=$'\e[36m' reset=$'\e[0m'
else
    bold='' dim='' green='' yellow='' cyan='' reset=''
fi

section() { printf '\n%s%s%s\n' "${bold}" "$1" "${reset}"; }
cmd() { printf '  %s%-46s%s %s\n' "${cyan}" "$1" "${reset}" "$2"; }

tool() {
    local icon=$1 name=$2 binary=$3 version
    if command -v "${binary}" >/dev/null 2>&1; then
        version=$("${@:4}" 2>/dev/null | head -n 1 | grep -oE '[0-9]+(\.[0-9]+)+' | head -n 1)
        printf '  %s %s%-10s%s %s✅ %s%s\n' "${icon}" "${bold}" "${name}" "${reset}" \
            "${green}" "${version:-installed}" "${reset}"
    else
        printf '  %s %s%-10s%s %s⚠️  missing — rebuild the container%s\n' "${icon}" "${bold}" \
            "${name}" "${reset}" "${yellow}" "${reset}"
    fi
}

login() {
    local icon=$1 name=$2 hint=$3
    shift 3
    if "$@"; then
        printf '  %s %s%-10s%s %s🔓 signed in%s\n' "${icon}" "${bold}" "${name}" "${reset}" \
            "${green}" "${reset}"
    else
        printf '  %s %s%-10s%s %s🔑 not signed in%s %s→ %s%s\n' "${icon}" "${bold}" "${name}" \
            "${reset}" "${yellow}" "${reset}" "${dim}" "${hint}" "${reset}"
    fi
}

claude_ready() {
    [[ -f "${HOME}/.claude/.credentials.json" || -n "${CLAUDE_CODE_OAUTH_TOKEN:-}" \
        || -n "${ANTHROPIC_API_KEY:-}" ]]
}
pi_ready() { [[ -s "${HOME}/.pi/agent/auth.json" ]]; }
codex_ready() { [[ -f "${HOME}/.codex/auth.json" || -n "${OPENAI_API_KEY:-}" ]]; }

cat <<EOF

${bold}  ♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜${reset}
${bold}  ♟ ♟ ♟ ♟ ♟ ♟ ♟ ♟${reset}    ${bold}Welcome to Chess! 👋${reset}
                     ${dim}Rust firmware · KiCad PCB · Blender CAD${reset}
  ♙ ♙ ♙ ♙ ♙ ♙ ♙ ♙
  ♖ ♘ ♗ ♕ ♔ ♗ ♘ ♖    ${dim}Your move. 🎉${reset}
EOF

section "🧰 Toolchain"
tool "🦀" "Rust" cargo cargo --version
tool "⚙️ " "Just" just just --version
tool "🐍" "Python" python3 python3 --version
tool "🧹" "Ruff" ruff ruff --version
tool "🔌" "KiCad" kicad-cli kicad-cli version
tool "🧊" "Blender" "${BLENDER_BIN:-blender}" "${BLENDER_BIN:-blender}" --version
tool "🥟" "Bun" bun bun --version
tool "🐳" "Docker" docker docker --version

section "🤖 Agents"
login "🧠" "Claude" "claude auth login" claude_ready
login "🥧" "Pi" "pi, then /login" pi_ready
login "📜" "Codex" "codex login" codex_ready
tool "🐑" "Herdr" herdr herdr --version

section "🚀 Start here"
cmd "just" "📋 list every repository recipe"
cmd "just precommit" "✅ the fast commit gate (runs on every commit)"
cmd "just quality" "🧹 lint and format-check every package"
cmd "just test" "🧪 test every package"
cmd "just check" "🏁 all domains, sequentially (slow)"

section "🔧 Hardware & firmware"
cmd "just pcb" "🔌 test, then generate PCB review output"
cmd "just cad" "🧊 test, then generate CAD renders"
cmd "just firmware-binary" "🦀 link the firmware for AArch64"
cmd "just --justfile <package>/justfile check" "🎯 one package at a time"

section "👥 Agent team"
cmd "just agents-doctor" "🩺 check tools and logins (no model calls)"
cmd "just agents" "🏟️  start the team (Claude Code or Pi)"
cmd "just agents-restart" "🔄 restart the team, task handoff kept"
cmd "just agents-stop" "🛑 stop the team"

section "📚 Read next"
printf '  📖 README.md   🤝 CONTRIBUTING.md   🏗️  docs/architecture.md   🛠️  docs/development.md\n'
printf '\n  %sShow this again any time with %sjust welcome%s%s ✨\n\n' "${dim}" "${cyan}" "${reset}" \
    "${reset}"
