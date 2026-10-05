# Chess agent team

Optional Herdr runtime alongside the existing [Pi setup](../../.pi/README.md).
The team runs in either Claude Code or Pi: in a terminal, `just agents` and
`just agents-reset` ask which one to use (Enter keeps the `fleet.toml` defaults,
which are Claude Code). `--harness claude|pi|codex` skips the question; menu actions
and non-interactive runs never ask and use `fleet.toml`.
All fourteen configured roles use Claude Code by default. The eight regular roles
are lead, portable Rust developer, firmware engineer, hardware engineer, mechanical
engineer, QA, reviewer and pushback. Manufacturing engineer, test engineer, DevOps
engineer, PM, upgrade reviewer and PR maker start on demand, with at most two alongside
the full default roster (ten active agents maximum).

Opus handles electrical/mechanical/DFM reasoning, lead decisions and review; Sonnet
handles bounded software/tooling/test work. See [team.md](team.md) for the ownership
matrix and interface handoffs. There is no student role, generic scenario role or
mandatory approval chain. Start only agents relevant to the task; roles start idle.
Starting the fleet may consume subscription/API usage.

## Setup

Rebuild/reopen the devcontainer after pulling these changes. The image pins
Claude Code 2.1.287 and checksum-verified Herdr 0.9.3. Post-create installs
Pi, Codex 0.159.3, Herdr's Claude/Codex/Pi hooks, Reviewr v0.39.0 and the Chess menu plugin.
`just agents-setup` repeats runtime integration setup (network required for Reviewr).
Reviewr is optional: a marketplace outage warns without blocking the container or team;
retry setup later to install the panel.
Setup never signs you in, starts agents, makes model calls, or pre-trusts the
checkout. Run `claude` once and accept workspace trust yourself on first use.
If startup is blocked or times out, the launcher keeps that pane for inspection instead
of destroying the dialog. Attach to the session, answer prompts yourself, then
`just agents-stop ROLE` and `just agents ROLE` to complete a clean startup/brief.

Login inside the container:

```sh
claude auth login
# Pi instead (or as well): run pi, then /login for its default provider
just agents-doctor --harness pi
# Optional alternate harness:
codex login
just agents-doctor
just agents-list
just agents lead developer --dry-run
just agents lead developer
# PCB/enclosure work without unrelated software roles:
just agents lead hardware-engineer mechanical-engineer
# Pi adapter/runtime work:
just agents lead firmware-engineer
# Or start the complete default team (asks Claude Code or Pi):
just agents
just agents --harness pi                # skip the question
```

With Pi, every role uses Pi's configured default model (`.pi/settings.json`), the
work kind's effort becomes `--thinking`, the brief is appended to the system prompt,
and the `subagent` tool is excluded so roles cannot spawn nested teams. Pi has no
permission prompts, so `--dangerous` changes nothing for it; Pi roles act without
asking. `up` keeps running roles in their original harness: use `--fresh` (or
`just agents-stop ROLE`) to switch.

Claude/Codex credentials and Herdr configuration use separate named Docker
volumes, not host credential bind mounts. Login survives a container rebuild,
not volume deletion. Host OAuth can instead be forwarded with
`CLAUDE_CODE_OAUTH_TOKEN`; never commit it. Pi's existing volumes/settings remain
unchanged. `ANTHROPIC_API_KEY` is also forwarded for Pi: unset it before container
creation if you want Claude subscription billing rather than API billing.
Doctor warns about API credentials; it does not make a model request.

## Lifecycle

```sh
just agents --no-attach                 # start/reuse without opening the UI
herdr --session chess                   # attach; Ctrl+B Q detaches, agents keep running
just agents reviewer --session chess    # add only a missing role
just agents pr-maker --no-attach        # only with a delivery assignment
just agents-stop pr-maker               # release an on-demand slot
just agents --fresh --no-attach         # new conversations, retain task checkpoint
just agents-reset --no-attach           # new conversations, clear task checkpoint
just agents-stop                       # close this team's workspace only
just agents-usage --hours 24            # local recorded tokens, not plan allowance
just agents-check                      # lint, format and offline regressions
just agents-test                       # just the offline regression suite
HERDR_TEST_BIN="$(command -v herdr)" just agents-test # isolated native API smoke tests
```

Use `--session NAME` on launcher commands for a separate named session. Do not
run duplicate sessions for the same task. Names permit ASCII letters, digits,
underscores and hyphens, starting with a letter/digit. `list`/`--dry-run` work
without installed providers or login. Mutations require a container. Workspace labels
include a stable checkout-path hash so another clone/worktree's team cannot be mistaken
for this one's. Herdr agent names remain server-scoped: use different sessions for
concurrent checkouts. Explicit named-session commands ignore inherited foreign socket,
workspace and machine settings; plugin actions retain their validated invoking context.
If you already launched the earlier generic `chess-team` roster, stop it in Herdr before
starting this checkout-bound roster; old roles are not automatically migrated/evicted.

`fleet.toml` owns model aliases, effort, provider adapter, role map and cap.
To use Codex for a work kind set `harness = "codex"`, `model = "-"`, and a
supported effort such as `medium`, then log in to Codex. Restart affected roles
to apply changes; `up` deliberately preserves existing conversations.
Per-role briefs and private reports/checkpoints live in `target/agents/<session>`.
The launcher locks each session during mutations, enforces the cap across
incremental starts, rejects foreign role collisions and cleans definitively failed
new panes. Blocked/timed-out startup panes are kept for operator intervention, not
silently accepted or retried.
Menu actions are bound to their invoking session/socket/workspace.

Provider permission checks remain enabled. If you knowingly want unattended
permission bypass, pass `--dangerous` to `agents`/`agents-reset` explicitly.
A container is not a complete sandbox: agents still see credentials, mounted
source, the network and the in-container Docker daemon. The menu never enables
bypass, and restarting without this flag restores ordinary permission behavior.

`just check`, `just quality` and the normal pre-commit hook include `agents-check`.
CI always runs offline tests; native smoke tests are opt-in, use temporary Git repositories
and isolated Herdr servers, and never launch a provider or make model requests.

Follow [team.md](team.md) and [AGENTS.md](../../AGENTS.md): one writer per file,
one Git owner, one expensive-check owner, and no publication before approval
when the user requests unstaged review. No automatic task dispatch or merging.

## Provenance

Launcher and local token reporting are adapted from
[`nicksan222/study`](https://github.com/nicksan222/study/tree/500b4c563c571db21e9a2f86d740506fbf816bed/.agents/team)
at `500b4c563c571db21e9a2f86d740506fbf816bed`; setup hook normalization follows
its devcontainer setup. The source MIT notice is retained in `LICENSE-MIT`.
The roster/briefs are Chess-specific: native PCB electronics, Blender mechanics,
Pi Linux firmware, DFM/prototype evidence, Linux/SPICE/mesh tests and Yocto/toolchains.
Study's learner/scenario roles, desktop-specific skills and third-party prompt plugins
are not imported. Portable persistence work follows the actual owning crate, not a
presumed Study database stack.
