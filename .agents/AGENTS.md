# Working in Chess

This is the canonical entry point for every coding harness; root and provider
entry points symlink here. Follow the user's
scope and delivery instructions; preserve unrelated work. Repository guidance
supplements the session's tool, permission and safety rules.

## Discover before changing

Treat source code, authoritative contracts and executable checks as the
authority. Instructions describe intent and how to find current examples; do
not assume an example, count, pin, part number or command flag is still current.

- Start with `git status --short` and the relevant owning sources, package
  README and checks. Consult the root `README.md`, `.github/CONTRIBUTING.md`
  and relevant `justfile`s when needed for context or commands.
- Use the harness skill catalog to discover matching skills; if unavailable,
  list `.agents/skills/*/SKILL.md` and read their `name` and `description`
  fields. Load matching instructions before changing the area they cover.
- Architecture is in `docs/architecture.md`; development commands and CI are in
  `docs/development.md`. Confirm behavior in implementation and tests before
  relying on prose, and update the owning guidance when a change invalidates it.
- Skip generated CAD/PCB output, `target/` and lockfiles during ordinary
  searches. Inspect them when the task concerns those artifacts.

## Boundaries

- `apps/firmware`: Raspberry Pi process, system integration, Yocto image.
- `crates/{chess,core,logger,menu,persistence}`: portable Rust logic and services.
- `hardware/shared`: authoritative physical, electrical and firmware contracts.
- `hardware/pcb`: KiCad generation, routing, SPICE and board validation.
- `hardware/cad`: Blender geometry and review renders.

Change authoritative contracts before regenerating artifacts. Do not hand-edit
generated CAD/PCB output or weaken tests to make hardware pass. Firmware pin
declarations are hand-maintained; a pin, power, stack or image change crossing
domains needs both sides agreed and verified, not a duplicate source of truth.
Automated checks do not prove a physical board is safe or manufactured
correctly. Do not flash hardware, order parts, publish fabrication files or
claim physical validation without explicit authorization.

## Runtime and verification

The reproducible toolchain is defined in `.devcontainer/` and
`rust-toolchain.toml`; do not copy version pins into instructions or install
missing tools ad hoc. Inside the container,
run commands directly; from a host checkout, use `devcontainer exec` when the
toolchain is absent. Report unavailable verification rather than inventing it.

- `just` lists workflows. Run focused package recipes first:
  `just --justfile <package>/justfile check`.
- `just quality` checks formatting and lints; `just precommit` is the commit
  gate run by `.githooks/pre-commit`; `just check` validates and generates
  across domains. PCB review is `just pcb`, CAD is `just cad`.
- Physical release (`just pcb-release`) and Yocto (`just firmware-check`,
  `just firmware`) are separate, explicit gates. Keep one owner for each
  expensive generation, Docker/QEMU or image run and reuse its result.
- Label evidence: datasheet calculation, unit test, SPICE, mesh/render, Linux
  simulation, AArch64 linkage, Yocto metadata/image or bench observation. None
  of the automated kinds proves electrical safety, magnet margin or printed fit.
- Preserve Git hooks and checks. Never bypass hooks or weaken gates, stage
  everything, stash or reset someone else's work, force-push or merge without
  authorization. Stage, commit, push or open PRs only within the user's
  delivery request; an explicit request for local or unstaged review wins over
  any normal PR workflow.

## Delegation and roles

The main session is the lead: it owns the overall solution, integration, Git
and user communication. For ambiguous or consequential work, define outcomes,
acceptance criteria, assumptions and scope against the project goals; challenge
unsupported assumptions and choose proportionate evidence before implementing.
Delegate bounded independent work only when it saves meaningful time or context,
using the least costly capable model available to the session; shared roles do
not prescribe provider models.

Discover role descriptions in `.agents/roles/*.md`; read the selected role and
include its path or full instructions in the brief. Give each worker its goal,
permitted paths, acceptance evidence and stopping point. Use native custom
agents when available; otherwise pass the same shared role to a general worker.
If delegation is unavailable, apply the role as an explicit inline pass and
report that it was not independent.

Roles are leaf workers: stay within the assigned paths, do not delegate, and
report changed files, checks, interface changes and remaining risks. Honor each
role's read-only and side-effect limits; prose is not a sandbox, so review changes and evidence before accepting a
report. Keep one writer per file and one owner for combined verification.
Neither a role nor a skill grants permission for extra Git actions, hardware
actions, purchases or publication.

## Maintaining this tooling

All tracked agent instructions and configuration are owned by `.agents`;
root and provider-facing files are symlinks into it. See `.agents/README.md` for the adapter
layout and how to add or rename a skill or role. Do not copy shared
instructions into provider configuration.
