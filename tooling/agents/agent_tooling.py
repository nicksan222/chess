"""Validate shared agent skills/roles and keep native harness adapters in sync.

`.agents/skills` and `.agents/roles` are the only sources. This module checks
them, the instruction entry points that reference them and the Claude/Codex
adapters generated from them. Run with `--sync` to create missing links and
rewrite drifted generated adapters; validation alone never writes.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import unquote

ENTRY_POINTS = ("CLAUDE.md", "GEMINI.md", ".github/copilot-instructions.md")
INSTRUCTION_FILES = ("AGENTS.md", *ENTRY_POINTS, ".agents/README.md")
SKILL_NAME = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


@dataclass(frozen=True)
class Finding:
    file: str
    message: str

    def __str__(self) -> str:
        return f"{self.file}: {self.message}"


@dataclass(frozen=True)
class Role:
    name: str
    description: str
    read_only: bool
    skills: tuple[str, ...] = ()


@dataclass(frozen=True)
class Targets:
    roles: frozenset[str]
    skills: frozenset[str]
    recipes: frozenset[str]


# ── Frontmatter ──────────────────────────────────────────────────────────────


def split_frontmatter(source: str) -> tuple[str, str] | None:
    match = re.match(r"^---\r?\n(.*?)\r?\n---\r?\n?(.*)$", source, re.DOTALL)
    return (match[1], match[2]) if match else None


def _scalar(raw: str) -> object:
    value = raw.strip()
    if value.startswith('"'):
        return json.loads(value)
    if value.startswith("'") and value.endswith("'") and len(value) > 1:
        return value[1:-1].replace("''", "'")
    return {"true": True, "false": False}.get(value, value)


def parse_frontmatter(text: str) -> dict[str, object]:
    """Parse the flat YAML subset used by skills and roles.

    Supports `key: scalar` (plain, quoted, true/false), `key: |`/`>` blocks and
    `key:` followed by `  - item` lists. Anything else is rejected rather than
    silently misread; nested provider metadata stays out of shared files.
    """
    data: dict[str, object] = {}
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        match = re.match(r"^([A-Za-z][\w-]*):(?:\s+(.*))?$", line)
        if not match:
            raise ValueError(f"unsupported frontmatter line: {line!r}")
        key, value = match[1], (match[2] or "").strip()
        if key in data:
            raise ValueError(f"duplicate frontmatter key: {key}")
        if value in {"|", ">", "|-", ">-"}:
            block: list[str] = []
            while index < len(lines) and (
                not lines[index].strip() or lines[index][0] == " "
            ):
                block.append(lines[index].strip())
                index += 1
            joiner = "\n" if value.startswith("|") else " "
            data[key] = joiner.join(block).strip()
        elif value:
            data[key] = _scalar(value)
        else:
            items: list[object] = []
            while index < len(lines) and re.match(r"^\s+-\s", lines[index]):
                items.append(_scalar(lines[index].strip()[1:]))
                index += 1
            data[key] = items
    return data


# ── Shared skills and roles ──────────────────────────────────────────────────


def _nonempty(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


def check_skill(file: str, name: str, frontmatter: dict[str, object]) -> list[Finding]:
    """Validate the Agent Skills core, not a provider's evolving extensions."""
    messages = []
    if frontmatter.get("name") != name:
        messages.append(f"name must match the directory ({name})")
    if not SKILL_NAME.match(name) or len(name) > 64:
        messages.append("name must be lowercase kebab-case and at most 64 characters")
    description = frontmatter.get("description")
    if not _nonempty(description):
        messages.append("description is required")
    elif len(str(description)) > 1024:
        messages.append("description must be at most 1024 characters")
    return [Finding(file, message) for message in messages]


def check_role(
    file: str,
    name: str,
    frontmatter: dict[str, object],
    body: str,
    skills: frozenset[str],
) -> list[Finding]:
    findings = check_skill(file, name, frontmatter)
    if not isinstance(frontmatter.get("read-only"), bool):
        findings.append(Finding(file, "read-only must be true or false"))
    required = frontmatter.get("skills")
    if required is not None:
        if not isinstance(required, list) or not all(
            _nonempty(skill) for skill in required
        ):
            findings.append(Finding(file, "skills must be a list of skill names"))
        else:
            findings.extend(
                Finding(file, f"skills: no .agents/skills/{skill}/SKILL.md")
                for skill in required
                if skill not in skills
            )
    if not body.strip():
        findings.append(Finding(file, "the role body is empty"))
    return findings


def role_from(frontmatter: dict[str, object]) -> Role:
    return Role(
        name=str(frontmatter["name"]),
        description=str(frontmatter["description"]),
        read_only=bool(frontmatter["read-only"]),
        skills=tuple(str(skill) for skill in frontmatter.get("skills") or ()),
    )


# ── Generated adapters ───────────────────────────────────────────────────────


def role_instructions(role: Role) -> str:
    return (
        f"Read `AGENTS.md` and `.agents/roles/{role.name}.md` before acting. Follow the role's\n"
        "scope and the lead's brief. Do not delegate further.\n"
    )


def codex_ownership(role: Role) -> str:
    return (
        f"# Generated by just sync-agents; edit .agents/roles/{role.name}.md instead."
    )


def render_claude_agent(role: Role) -> str:
    denied = "Edit, Write, NotebookEdit, Agent" if role.read_only else "Agent"
    skills = "".join(f"  - {skill}\n" for skill in role.skills)
    if skills:
        skills = "skills:\n" + skills
    return (
        f"---\nname: {role.name}\ndescription: {json.dumps(role.description)}\n"
        f"disallowedTools: {denied}\n{skills}---\n\n{role_instructions(role)}"
    )


def render_codex_agent(role: Role) -> str:
    return (
        f"{codex_ownership(role)}\nname = {json.dumps(role.name)}\n"
        f"description = {json.dumps(role.description)}\n"
        f"developer_instructions = {json.dumps(role_instructions(role))}\n"
    )


@dataclass(frozen=True)
class Link:
    file: str
    target: str


@dataclass(frozen=True)
class Generated:
    file: str
    content: str
    ownership: str


Adapter = Link | Generated


def adapters(roles: list[Role], skill_names: list[str]) -> list[Adapter]:
    result: list[Adapter] = [Link(file, "AGENTS.md") for file in ENTRY_POINTS]
    result += [
        Link(f".claude/skills/{name}", f".agents/skills/{name}") for name in skill_names
    ]
    for role in roles:
        result.append(
            Generated(
                f".claude/agents/{role.name}.md",
                render_claude_agent(role),
                role_instructions(role).strip(),
            )
        )
        result.append(
            Generated(
                f".codex/agents/{role.name}.toml",
                render_codex_agent(role),
                codex_ownership(role),
            )
        )
    return result


def _linked_parent(root: Path, file: str) -> bool:
    parent = root
    for part in Path(file).parent.parts:
        parent = parent / part
        if parent.is_symlink() or (parent.exists() and not parent.is_dir()):
            return True
        if not parent.exists():
            return False
    return False


def adapter_status(root: Path, adapter: Adapter) -> str:
    """Return `valid`, `drift` (safe to regenerate) or `conflict` (local copy)."""
    if _linked_parent(root, adapter.file):
        return "conflict"
    path = root / adapter.file
    if not path.is_symlink() and not path.exists():
        return "drift"
    if isinstance(adapter, Link):
        if not path.is_symlink():
            return "conflict"
        resolved = (path.parent / os.readlink(path)).resolve()
        return "valid" if resolved == (root / adapter.target).resolve() else "conflict"
    if path.is_symlink() or not path.is_file():
        return "conflict"
    content = path.read_text(encoding="utf-8")
    if content == adapter.content:
        return "valid"
    return "drift" if adapter.ownership in content else "conflict"


def write_adapter(root: Path, adapter: Adapter) -> None:
    path = root / adapter.file
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(adapter, Link):
        path.symlink_to(os.path.relpath(root / adapter.target, path.parent))
    else:
        path.write_text(adapter.content, encoding="utf-8")


def sync_adapters(
    root: Path, roles: list[Role], skill_names: list[str], write: bool
) -> list[Finding]:
    """Preflight the full set before writing, preserving conflicting local files."""
    states = [
        (adapter, adapter_status(root, adapter))
        for adapter in adapters(roles, skill_names)
    ]
    conflicts = [adapter for adapter, status in states if status == "conflict"]
    if conflicts:
        return [
            Finding(
                adapter.file,
                "refusing to replace a local copy or write through a conflicting link or "
                "parent; reconcile it manually",
            )
            for adapter in conflicts
        ]
    drifted = [adapter for adapter, status in states if status == "drift"]
    if write:
        for adapter in drifted:
            write_adapter(root, adapter)
        return []
    return [
        Finding(
            adapter.file, "adapter differs from its shared source; run just sync-agents"
        )
        for adapter in drifted
    ]


# ── References in instructions ───────────────────────────────────────────────


def code_snippets(markdown: str) -> tuple[list[str], str]:
    """Split fenced blocks and inline code spans from prose."""
    code: list[str] = []

    def fence(match: re.Match[str]) -> str:
        code.append(match[2])
        return ""

    def span(match: re.Match[str]) -> str:
        code.append(match[1])
        return "``"

    prose = re.sub(
        r"^(```|~~~)[^\n]*\n(.*?)^\1[ \t]*$",
        fence,
        markdown,
        flags=re.MULTILINE | re.DOTALL,
    )
    prose = re.sub(r"`([^`\n]+)`", span, prose)
    return code, prose


def relative_links(markdown: str) -> list[str]:
    """Relative Markdown link targets (no URLs, anchors or absolute paths)."""
    _, prose = code_snippets(markdown)
    targets = []
    for match in re.finditer(
        r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)", prose
    ):
        target = match[1].split("#")[0]
        if target and not re.match(r"^(?:[a-z][\w+.-]*:|/)", target, re.IGNORECASE):
            targets.append(unquote(target))
    return targets


def just_recipes(justfile: str) -> set[str]:
    recipes = set(
        re.findall(r"^@?([A-Za-z_][\w-]*)(?:\s[^:\n]*)?:(?!=)", justfile, re.MULTILINE)
    )
    recipes |= set(re.findall(r"^alias\s+([\w-]+)\s*:=", justfile, re.MULTILINE))
    return recipes - {"set", "export", "import", "mod"}


def _recipe_problems(
    root: Path, snippets: list[str], recipes: frozenset[str]
) -> list[str]:
    problems = []
    command = re.compile(
        r"(?:^|[\s;&|(])just\s+(?:--justfile\s+(\S+)\s+)?([a-z][\w-]*)", re.MULTILINE
    )
    for snippet in snippets:
        for justfile, recipe in command.findall(snippet):
            if not justfile:
                if recipe not in recipes:
                    problems.append(f"just {recipe}: no such justfile recipe")
                continue
            path = root / justfile
            # Placeholders such as `<package>/justfile` are documentation, not paths.
            if "<" in justfile or not path.is_file():
                continue
            if recipe not in just_recipes(path.read_text(encoding="utf-8")):
                problems.append(f"just --justfile {justfile} {recipe}: no such recipe")
    return problems


def _mention_problems(markdown: str, targets: Targets) -> list[str]:
    mentions = [
        (name, kind.lower())
        for name, kind in re.findall(
            r"`([\w-]+)`\s+(skill|role|subagent)s?\b", markdown, re.IGNORECASE
        )
    ]
    mentions += [
        (name, kind.lower())
        for kind, name in re.findall(
            r"\b(skill|role|subagent)\s+`([\w-]+)`", markdown, re.IGNORECASE
        )
    ]
    problems = []
    for name, kind in mentions:
        if kind == "skill" and name not in targets.skills:
            problems.append(f"skill {name}: no .agents/skills/{name}/SKILL.md")
        elif kind != "skill" and name not in targets.roles:
            problems.append(f"{kind} {name}: no .agents/roles/{name}.md")
    return problems


def dangling_references(
    root: Path, file: str, markdown: str, targets: Targets
) -> list[Finding]:
    code, _ = code_snippets(markdown)
    messages = _recipe_problems(root, code, targets.recipes) + _mention_problems(
        markdown, targets
    )
    return [Finding(file, message) for message in dict.fromkeys(messages)]


def repo_path_mentions(markdown: str, root_entries: set[str]) -> list[str]:
    """Backticked paths rooted at an existing top-level entry."""
    code, _ = code_snippets(markdown)
    paths = [
        snippet.strip()
        for snippet in code
        if re.match(r"^[\w.-]+(?:/[\w.-]+)*/?$", snippet.strip()) and "/" in snippet
    ]
    return list(
        dict.fromkeys(path for path in paths if path.split("/")[0] in root_entries)
    )


# ── Harness configuration ────────────────────────────────────────────────────


def check_settings(file: str, settings: object) -> list[Finding]:
    if not isinstance(settings, dict):
        return [Finding(file, "settings must be an object")]
    plugins = settings.get("enabledPlugins", {})
    marketplaces = settings.get("extraKnownMarketplaces", {})
    findings = []
    for plugin, enabled in plugins.items():
        marketplace = plugin.partition("@")[2]
        if not isinstance(enabled, bool):
            findings.append(
                Finding(file, f"enabledPlugins.{plugin} must be true or false")
            )
        elif not marketplace:
            findings.append(Finding(file, f"{plugin} must be named plugin@marketplace"))
        elif (
            marketplace != "claude-plugins-official" and marketplace not in marketplaces
        ):
            findings.append(
                Finding(file, f"{plugin} needs {marketplace} in extraKnownMarketplaces")
            )
    return findings


def check_mcp_config(file: str, config: object) -> list[Finding]:
    servers = config.get("mcpServers") if isinstance(config, dict) else None
    if not isinstance(servers, dict):
        return [Finding(file, "mcpServers must be an object")]
    findings = []
    for name, server in servers.items():
        if not isinstance(server, dict):
            findings.append(Finding(file, f"{name}: server must be an object"))
            continue
        if not _nonempty(server.get("command")) and not _nonempty(server.get("url")):
            findings.append(Finding(file, f"{name}: needs a command or url"))
        args = server.get("args")
        if args is not None and not (
            isinstance(args, list) and all(isinstance(arg, str) for arg in args)
        ):
            findings.append(Finding(file, f"{name}: args must be a list of strings"))
    return findings


# ── Repository check ─────────────────────────────────────────────────────────


class Checker:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.findings: list[Finding] = []
        self.root_entries = {entry.name for entry in root.iterdir()}

    def entries(self, directory: str) -> list[str]:
        path = self.root / directory
        if not path.is_dir():
            self.findings.append(Finding(directory, "shared directory is missing"))
            return []
        return sorted(entry.name for entry in path.iterdir())

    def markdown(self, file: str) -> tuple[dict[str, object], str] | None:
        try:
            parts = split_frontmatter((self.root / file).read_text(encoding="utf-8"))
            if not parts:
                raise ValueError("missing YAML frontmatter")
            return parse_frontmatter(parts[0]), parts[1]
        except (OSError, ValueError) as error:
            self.findings.append(Finding(file, str(error)))
            return None

    def json(self, file: str) -> object:
        try:
            return json.loads((self.root / file).read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            self.findings.append(Finding(file, f"invalid JSON: {error}"))
            return None

    def ignored(self, path: str) -> bool:
        result = subprocess.run(
            ["git", "check-ignore", "--quiet", path], cwd=self.root, check=False
        )
        return result.returncode == 0

    def references(self, file: str, body: str, targets: Targets) -> None:
        self.findings += dangling_references(self.root, file, body, targets)
        for path in repo_path_mentions(body, self.root_entries):
            if not (self.root / path).exists() and not self.ignored(path):
                self.findings.append(
                    Finding(file, f"{path} does not exist; update the source reference")
                )
        base = (self.root / file).parent
        for link in relative_links(body):
            if not os.path.exists(os.path.normpath(base / link)):
                self.findings.append(
                    Finding(file, f"link target {link} does not exist")
                )

    def run(self, write: bool) -> tuple[list[Role], list[str]]:
        skill_names = self.entries(".agents/skills")
        role_files = [
            name for name in self.entries(".agents/roles") if name.endswith(".md")
        ]
        justfile = self.root / "justfile"
        targets = Targets(
            roles=frozenset(name.removesuffix(".md") for name in role_files),
            skills=frozenset(skill_names),
            recipes=frozenset(just_recipes(justfile.read_text(encoding="utf-8"))),
        )

        for name in skill_names:
            file = f".agents/skills/{name}/SKILL.md"
            skill = self.markdown(file)
            if not skill:
                continue
            frontmatter, body = skill
            self.findings += check_skill(file, name, frontmatter)
            if not body.strip():
                self.findings.append(Finding(file, "the skill body is empty"))
            for path in sorted((self.root / ".agents/skills" / name).rglob("*.md")):
                relative = path.relative_to(self.root).as_posix()
                text = body if relative == file else path.read_text(encoding="utf-8")
                self.references(relative, text, targets)

        roles: list[Role] = []
        for entry in role_files:
            name = entry.removesuffix(".md")
            file = f".agents/roles/{entry}"
            role = self.markdown(file)
            if not role:
                continue
            frontmatter, body = role
            problems = check_role(file, name, frontmatter, body, targets.skills)
            self.findings += problems
            self.references(file, body, targets)
            if not problems:
                roles.append(role_from(frontmatter))

        # Synchronization uses only validated inputs. Validation mode is read-only.
        if not write or not self.findings:
            self.findings += sync_adapters(self.root, roles, skill_names, write)

        for file in INSTRUCTION_FILES:
            path = self.root / file
            if path.exists():
                self.references(file, path.read_text(encoding="utf-8"), targets)
            else:
                self.findings.append(
                    Finding(file, "instruction entry point is missing")
                )

        for file, check in (
            (".mcp.json", check_mcp_config),
            (".claude/settings.json", check_settings),
        ):
            if (self.root / file).exists():
                config = self.json(file)
                if config is not None:
                    self.findings += check(file, config)

        for name in self.entries(".claude/skills"):
            path = self.root / ".claude/skills" / name
            if path.is_symlink() and not path.exists():
                self.findings.append(
                    Finding(
                        f".claude/skills/{name}",
                        "broken skill adapter; remove it or restore the shared skill",
                    )
                )

        # Catch orphaned generated adapters without forbidding personal/native config.
        for directory, suffix in (
            (".claude/agents", ".md"),
            (".codex/agents", ".toml"),
        ):
            if not (self.root / directory).is_dir():
                continue
            for entry in self.entries(directory):
                path = self.root / directory / entry
                if not entry.endswith(suffix) or not path.is_file():
                    continue
                orphan = entry.removesuffix(suffix) not in targets.roles
                if orphan and ".agents/roles/" in path.read_text(encoding="utf-8"):
                    self.findings.append(
                        Finding(
                            f"{directory}/{entry}",
                            "adapter has no shared role; remove or reconcile it",
                        )
                    )
        return roles, skill_names


def main(argv: list[str] | None = None) -> int:
    args = sys.argv[1:] if argv is None else argv
    write = "--sync" in args
    root = Path(
        subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
    )
    checker = Checker(root)
    roles, skills = checker.run(write)
    for finding in checker.findings:
        print(finding, file=sys.stderr)
    if checker.findings:
        return 1
    suffix = " Adapters synchronized." if write else ""
    print(
        f"Agent tooling is valid: {len(roles)} shared roles, {len(skills)} skills, "
        f"adapters and references.{suffix}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
