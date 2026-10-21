# Shared coding-agent tooling

`AGENTS.md` is the repository entry point. Skills and roles have a single source:

| Location | Purpose |
| --- | --- |
| `.agents/skills/*/SKILL.md` | Agent Skills instructions and bundled references |
| `.agents/roles/*.md` | Shared subagent briefs with name, description, read-only intent and optional required skills |
| `.claude/skills/*` | Relative symlinks to the canonical skill folders |
| `.claude/agents/*.md` | Thin Claude wrappers that read the shared roles |
| `.codex/agents/*.toml` | Thin Codex wrappers that read the shared roles |
| `CLAUDE.md`, `GEMINI.md`, `.github/copilot-instructions.md` | Relative symlinks to `AGENTS.md` for harnesses with other instruction filenames |

Codex discovers repository skills in `.agents/skills`; Claude discovers the
linked skill folders. Both have native role adapters. Other harnesses can read
the same files through `AGENTS.md`; automatic discovery and delegation depend
on their version and capabilities. A harness that does not load any entry point
must be told to read `AGENTS.md` once. There is no universal subagent or
permission format, and no team launcher: the invoking session is the lead.

## Authoring and discovery

List the actual skill and role files and read their frontmatter to select one.
Do not maintain a second roster or copy prompts into adapters. Skill
frontmatter uses the Agent Skills core (`name`, `description`). A role has
`name`, `description`, `read-only: true|false` and an optional list of existing
`skills`. All roles are leaves. Read-only describes source-editing intent;
delivery roles still need explicit authorization for their Git side effects.

Models, effort, provider routing and permissions belong to the invoking
session. Native restrictions help but role prose is not a security boundary.
Write guidance that points at current sources, contracts, tests and recipes
instead of copying numbers, part lists, pins or versions that will go stale.

## Maintenance

Adapters are thin and written by hand; keep them in step with their source in
the same change:

- New skill: add `.agents/skills/<name>/SKILL.md` and a relative link
  `.claude/skills/<name> -> ../../.agents/skills/<name>`.
- New role: add `.agents/roles/<name>.md`, then copy an existing wrapper in
  `.claude/agents/` and `.codex/agents/` and change only `name`, `description`
  and the role path. Read-only roles deny `Edit, Write, NotebookEdit, Agent` in
  the Claude wrapper; writable roles deny only `Agent`.
- Renamed or removed role or skill: rename or delete its wrappers and link too.
- When source changes invalidate guidance, update that guidance in the same
  change.
- Skill links need a checkout with symlinks enabled. Without them, use direct
  `.agents/skills` discovery instead of maintaining independent copies.

Personal plugins, models, providers, MCP servers and credentials stay in local
or user configuration (`.claude/settings.local.json`, `.codex/config.toml`).

## Adapter references

Adapters use the minimum documented format; check the current documentation
before extending them:

- [Agent Skills specification](https://agentskills.io/specification)
- [Codex skill discovery](https://developers.openai.com/codex/skills)
- [Codex custom agents](https://developers.openai.com/codex/subagents)
- [Claude skills](https://code.claude.com/docs/en/skills)
- [Claude subagents](https://code.claude.com/docs/en/sub-agents)
