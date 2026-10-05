# Chess contributor agents

Read `README.md`, `CONTRIBUTING.md`, and the relevant package README before editing.
Architecture is in `docs/architecture.md`; development commands are in
`docs/development.md`. Use the devcontainer for reproducible hardware checks.

## Boundaries

- `apps/firmware`: Raspberry Pi process, system integration, Yocto image.
- `crates/{chess,core,logger,menu,persistence}`: portable Rust logic and services.
- `hardware/shared`: authoritative physical, electrical and firmware contracts.
- `hardware/pcb`: KiCad generation, routing, SPICE and board validation.
- `hardware/cad`: Blender geometry and review renders.

Change authoritative contracts before regenerating artifacts. Do not hand-edit generated
CAD/PCB output or weaken tests to make hardware pass. Automated checks do not prove a
physical board is safe or manufactured correctly. Do not flash hardware, order parts,
publish fabrication files, or claim physical validation without explicit authorization.

## Validation

Use focused package recipes first: `just --justfile <package>/justfile check`.
`just quality` checks formatting/lints; `just precommit` is the commit gate;
`just check` validates and generates across domains. PCB review is `just pcb`, CAD is
`just cad`. Physical release (`just pcb-release`) and Yocto (`just firmware-check`,
`just firmware`) are separate, explicit gates. Commits run `.githooks/pre-commit`.
Agent tooling lint/format/tests: `just agents-check` (included in the commit gate).
Existing Pi tooling: `bun run --cwd .pi check`.

## Working agreement

Preserve unrelated changes. Never stage everything, stash/reset someone else's work,
bypass hooks, force-push or merge without authorization. An explicit request for local
or unstaged review wins over any normal PR workflow: do not stage, commit, push or open
that PR until the user approves.

Only delegate when the user authorizes it. Pi remains supported alongside Claude Code;
Herdr is an optional terminal/team runtime, not a replacement for Pi's governed subagent
protocol. Do not silently move a failed Pi workflow to another runner.

For authorized Herdr teams, read `.agents/team/team.md` and your assigned role brief.
`just agents-list` shows the roster; `just agents-doctor` checks tools/login without a
model request. `just agents lead developer` starts a small software team;
`just agents lead hardware-engineer mechanical-engineer` starts a hardware/fit team.
`just agents` asks whether to run the team in Pi or Claude Code (`--harness` skips
it) and starts eight default roles: lead, developer, firmware engineer, hardware
engineer, mechanical engineer, QA, reviewer and pushback. Manufacturing, test engineering,
DevOps, PM, upgrade review and PR delivery are on demand; the cap is ten active agents.
There is no student role or per-domain team. One writer per file, one Git owner and one
expensive-check owner. Idle agents wait for concrete assignments; never create nested
teams or exceed the cap. Cross-domain pin/power/stack/image changes require an explicit
interface handoff between the relevant engineers, not a duplicate source of truth.
