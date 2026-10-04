#!/usr/bin/env python3
"""Install runtime Herdr integrations; never trust a workspace or start a model."""

import json
import subprocess
from pathlib import Path


def portable_claude_hooks(home):
    """Normalize installer commands and deduplicate hooks on repeated setup."""
    path = home / ".claude/settings.json"
    if not path.exists():
        return
    settings = json.loads(path.read_text())
    installed = {
        f'bash "{home}/.claude/hooks/herdr-agent-state.sh" session',
        f"bash '{home}/.claude/hooks/herdr-agent-state.sh' session",
    }
    for event, groups in settings.get("hooks", {}).items():
        unique = []
        for group in groups:
            for hook in group.get("hooks", []):
                if hook.get("command") in installed:
                    hook["command"] = (
                        'bash "$HOME/.claude/hooks/herdr-agent-state.sh" session'
                    )
            if group not in unique:
                unique.append(group)
        settings["hooks"][event] = unique
    path.write_text(json.dumps(settings, indent=2) + "\n")


def main():
    if not (Path("/.dockerenv").exists() or Path("/run/.containerenv").exists()):
        raise SystemExit("run setup inside the devcontainer")
    home = Path.home()
    for directory in (".claude", ".codex", ".config/herdr"):
        (home / directory).mkdir(parents=True, exist_ok=True)
    for provider in ("claude", "codex"):
        subprocess.run(["herdr", "integration", "install", provider], check=True)
    portable_claude_hooks(home)
    reviewr = subprocess.run(
        [
            "herdr",
            "plugin",
            "install",
            "persiyanov/herdr-reviewr",
            "--ref",
            "v0.39.0",
            "--yes",
        ],
        check=False,
    )
    if reviewr.returncode:
        print(
            "warning: optional Reviewr installation failed; retry just agents-setup when GitHub is reachable"
        )
    subprocess.run(
        ["herdr", "plugin", "link", str(Path(__file__).resolve().parent)], check=True
    )
    for tool in ("claude", "codex", "herdr"):
        subprocess.run([tool, "--version"], check=True)
    print(
        "Herdr configured. Run claude auth login (or codex login), then just agents-doctor."
    )


if __name__ == "__main__":
    main()
