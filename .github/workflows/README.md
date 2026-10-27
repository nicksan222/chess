# Workflows

This directory owns GitHub Actions workflow definitions:

- `ci.yml` runs Hardware and Quality on `main` and `v*` tags, and
  calls `firmware.yml` with publish enabled only for release tags;
- `pr.yml` runs those same checks on pull requests, plus Firmware checks
  (Yocto metadata and the AArch64 binary), posts one updated comment when PCB
  components, wiring, placement, rules, or copper change, and provides the
  `Required checks` branch-protection gate;
- `hardware.yml`, `quality.yml`, and `firmware-check.yml` are reusable domain
  workflows that group those jobs in the Actions graph;
- `firmware.yml` is the full image build, started weekly, manually, or by a gated release-tag CI run; and
- `dependabot-automerge.yml` queues trusted Dependabot updates for squash merge
  after branch protection reports every required check green.

`pr.yml` starts with a `Changed scopes` job that runs
`.github/scripts/changed-scopes.sh` on the files the pull request changes since
it branched (a three-dot diff from the merge base, so commits that later land on
the base branch never count). Documentation-only changes skip every job
including the container prebuild. `apps/`, `crates/`, Cargo files, `clippy.toml`
and `deny.toml` run Quality and Firmware checks without Hardware. In Hardware,
`hardware/pcb` runs the PCB review and `hardware/cad` runs CAD against the
checked-in PCB export; `hardware/shared` runs both. After a PCB-only change,
CAD (Blender) runs only if the review regenerated the export it consumes
(`chess-board.glb`, `3d-models.json`, `pcb-components.json`,
`chess-board.kicad_pcb`) differently from the merge base, and the PR report
runs only when the PCB was reviewed. Repository lint configuration
(`tooling/`, ast-grep, typos and EditorConfig files, `.githooks/`)
run offline Quality alone, without Rust tests or network dependency audits.
`pyproject.toml` runs both hardware pipelines so pytest policy changes exercise
the affected tests. Any other path (workflows, the dev
container, the root `justfile`, new directories) runs everything, so unknown
files fail safe. `Required checks` accepts skipped jobs but still fails on any
failed or cancelled one. Pushes to `main` always run the full set.

Workflows invoke the same package-local `justfile` capabilities used by
developers. Workflow YAML contains only scheduling, caching, artifact,
permission, and release policy.

`hardware.yml` runs PCB review followed by CAD checks in one `🧩 PCB → CAD` job.
The job prepares one container from the pinned image and both steps execute in
that same container and workspace. CAD consumes the
checked native KiCad model produced by PCB review; PCB failure prevents CAD
from starting. Separate `pcb-generated` and `cad-generated` artifacts are
uploaded only when their generation steps succeed, so failed builds cannot
publish the checkout's older generated files as new review output. Missing expected
artifact files fail the upload instead of producing a successful warning.

PR reports compare freshly generated PCB output with the pull request's base
commit. CI calls the same `just --justfile hardware/pcb/justfile pr-report <ref>`
recipe available locally. Reports include ERC/DRC results and links to complete
generated artifacts. Pull requests without a semantic PCB change stay quiet;
forked pull requests keep the report in the job summary because GitHub withholds
write tokens. Physical measurements remain a separate release requirement.

`quality.yml` runs formatting, compilation, lints, documentation, pin/timing
patterns and portable crate boundaries. Rust tests run in the same container and
Cargo cache with one `just rust-test` invocation across the workspace. The
separate dependency job checks advisories, licences and sources without repeating
the global bans already checked by offline quality; it also runs `cargo shear`
and `pip-audit`. Rust tests and dependency audits run for Rust and broad changes.

Quality always lints every package, regardless of hardware change scopes. Hardware
review is independently complete: its first shared-contract check prepares the
container, PCB review runs lint and harness/catalog checks before generation
records the electrical suite, and CAD runs lint, tests and generation against
that export. Standalone
package `check` recipes retain their complete prerequisites. Branch protection
uses the PR workflow's `Required checks` aggregator rather than per-crate jobs.
