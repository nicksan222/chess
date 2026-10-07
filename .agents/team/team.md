# Chess engineering team

Read `AGENTS.md`, your role brief and the owning package documentation. Work in the
devcontainer. This is a physical chessboard driven by one Pi Linux process, with native
KiCad electrical design and Python-generated Blender mechanics—not a desktop study app.

## Roster and ownership

The default roster has eight roles. Availability is not a requirement to use every role:
small tasks should start only the needed agents. At most ten agents may run together,
leaving two concurrent slots for the six on-demand roles. The lead chooses those roles
for concrete outcomes; do not auto-evict workers, create per-domain/nested teams or raise
the cap without operator approval. Start a missing role with `python3 .agents/team/agents.py up <role> --no-attach`.

| Role | Responsibility | Normal authoring scope (only assigned files) |
| --- | --- | --- |
| lead | Requirements, interface decisions, integration and Git | Checkpoint, integration fixes |
| developer | Portable chess/menu/core/persistence/logger logic | `crates/` and callers agreed with firmware |
| firmware-engineer | Pi runtime, typed events, Linux device/network adapters | `apps/firmware/src/` and assigned tests |
| hardware-engineer | Circuit/power/pins, native PCB/connectivity/routing | `hardware/pcb/board/`, shared electrical contracts |
| mechanical-engineer | Enclosure/tile plate, tolerance/optical/assembly stack | `hardware/cad/`, shared dimensions |
| qa | Independent behavior/evidence verification | Reports; assigned validation execution |
| reviewer | Read-only correctness/contracts/regression review | Reports |
| pushback | Read-only challenge to architecture and physical assumptions | Reports |
| manufacturing-engineer (on demand) | DFM, sourcing, assembly/prototype/release evidence | Reports; explicitly assigned source/docs |
| test-engineer (on demand) | Test harnesses, negative cases, reproducible fixtures | Assigned test paths |
| devops-engineer (on demand) | Devcontainer, CI, toolchain, Yocto packaging | `.devcontainer/`, `.github/`, tooling, Yocto |
| pm (on demand) | Product acceptance and scope decisions | Reports |
| upgrade-reviewer (on demand) | Persisted data, contract and contributor upgrade risks | Reports |
| pr-maker (on demand) | Authorized Git/PR delivery using existing evidence | Explicitly handed-off Git paths |

These are responsibility boundaries, not blanket write permission. The lead assigns the
question/outcome, allowed files, acceptance check and stopping point. One writer per
file, one Git owner and one expensive-check owner. Reviewers/QA/pushback do not modify
implementation by default. Unassigned agents stay idle and send no status prompts.

## Interface changes

- Electronics → firmware: share net/pin identities, voltage/polarity, timing, Hall-bank
  addresses/mapping, LED order and brightness/power limits. Pi pin declarations are
  hand-maintained; coordinate both sides rather than inventing PCB-to-Rust generation.
- PCB → mechanics: share populated heights, keepouts, supports, holes, connector access
  and magnet/sensor/LED stack. Only agreed cross-domain measurements belong in
  `hardware/shared/dimensions.py`; tool behavior stays with its domain.
- Design → manufacturing: confirm exact approved parts, footprint/process compatibility,
  print/board tolerance and assembly/prototype acceptance. A render or clean DRC does
  not authorize a part substitution or fabrication.
- Runtime → image: coordinate required devices/kernel/packages/services between firmware
  and DevOps. A host/VM test, AArch64 link and Yocto image validate different boundaries.

For such a change, the lead identifies the affected peer, agrees the interface, assigns
one writer for each shared file, and includes the peer's evidence in review. Do not pass
broad ownership of `hardware/shared` to two engineers at once. Verify current code and
exact datasheets: historical documentation may contain obsolete counts or claims.

## Execution and evidence

Work in small slices: implement, focused test, report, read-only review, fix, then the
next slice. No fixed approval chain; use the perspectives relevant to the changed risk.
Never hand-edit generated hardware output, weaken checks or reproduce a failure by
resetting someone else's work. Generated PCB/CAD sets have one assigned producer.

Run focused package checks before combined validation. The lead grants one runner for
PCB `review`, CAD generation, Docker/QEMU E2E and Yocto tasks, then reuses the results.
Full PCB `release`, Yocto image builds, physical flashing, vendor uploads and purchasing
are separate authorized actions, not routine QA. Missing physical evidence remains a
blocker; never replace it with synthetic measurements or relaxed validation.

Every report labels its evidence: source/datasheet calculation, software unit test,
SPICE, mesh/render, Linux simulation, AArch64 linkage, Yocto metadata/image or actual
operator/bench observation. Record code/diff identity, exact inputs/commands, result and
untested limits. None of the automated categories proves physical electrical safety,
Hall/magnet margin, printed fit or a working manufactured board.

Write reports to the `Reports:` path in your brief as `<role>-<topic>.md`. Send the file
as one quoted argument; never paste arbitrary text into a shell command:

```sh
session=chess # replace with the session in your brief
report=target/agents/"$session"/reports/hardware-engineer-result.md
herdr --session "$session" agent prompt lead "$(cat -- "$report")"
```

Only lead talks to the user and updates `task.md`: objective, starting branch/preexisting
changes, interface decisions, owned files/check runner, current step, evidence and next
action (under 60 lines). Inspect the current diff before recovering a checkpoint or
reusing test-engineer fixtures. Reports/checkpoints are gitignored under
`target/agents/<session>`. Old evidence is a pointer to revalidate, not a current fact.

Herdr's sidebar owns status. Do not poll or wake models for progress. Send blockers once
with a concrete decision needed. Lead may inspect/re-brief a stalled pane. Do not answer
provider permission/trust dialogs on the user's behalf or silently enable bypass.

## Delivery

Lead verifies the combined result and hands PR maker exclusive Git ownership only when
publication is authorized. Handoff includes objective, owned paths, base/head/remote,
diff/commit identity, check evidence, interface/review findings and physical limitations.
Local-only/unstaged instructions forbid staging, committing, pushing and opening a PR
until the user explicitly approves. Never auto-merge or sweep unrelated changes.

`fleet.toml` owns models/effort: Opus for electrical/mechanical/DFM reasoning, lead and
review; Sonnet for bounded software/tooling/test tasks. `just agents-usage` reports local
recorded Claude tokens, not remaining allowance; Claude Code `/usage` is authoritative.
