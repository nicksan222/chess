# Shared coding-agent tooling

All tracked agent instructions and configuration live here. Provider-facing
files are relative symlinks, so edit their targets under `.agents`:

- `AGENTS.md`: shared instructions; linked from root `AGENTS.md`, `CLAUDE.md`,
  `GEMINI.md` and `.github/copilot-instructions.md`.
- `roles/*.md`: canonical roles, linked directly from `.claude/agents/`.
  Frontmatter includes Claude's `disallowedTools` restriction.
- `skills/*/SKILL.md`: canonical skills; `.claude/skills/*` links to these folders.
  Codex discovers `.agents/skills` directly.
- `adapters/codex/*.toml`: Codex's required native format, linked from
  `.codex/agents/`. These small adapters reference the canonical role Markdown;
  keep their discovery name and description aligned with the role.
- `adapters/claude-settings.json`: shared Claude settings, linked from
  `.claude/settings.json`.

Use the harness catalog or file frontmatter for discovery. Other harnesses can
read the canonical sources directly. When adding, renaming or removing a role
or skill, maintain its links and any Codex adapter in the same change. Read-only
Claude roles deny `Edit, Write, NotebookEdit, Agent`; writable roles deny `Agent`.
Native restrictions assist but do not replace the lead's scope and permissions.

Checkouts must preserve symlinks for native discovery. Keep personal models,
providers, MCP servers and credentials in ignored local or user configuration.

Adapter formats: [Agent Skills](https://agentskills.io/specification),
[Codex skills](https://developers.openai.com/codex/skills),
[Codex subagents](https://developers.openai.com/codex/subagents),
[Claude skills](https://code.claude.com/docs/en/skills) and
[Claude subagents](https://code.claude.com/docs/en/sub-agents).
