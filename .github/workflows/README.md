# Workflows

This directory owns GitHub Actions workflow definitions:

- `ci.yml` runs Hardware, Quality, and Pi harness on `main` and `v*` tags, and
  calls `firmware.yml` with publish enabled only for release tags;
- `pr.yml` runs those same checks on pull requests, plus Firmware checks
  (Yocto metadata and the AArch64 binary), posts one updated comment when PCB
  components, wiring, placement, rules, or copper change, and provides the
  `Required checks` branch-protection gate;
- `hardware.yml`, `quality.yml`, and `firmware-check.yml` are reusable domain
  workflows that group those jobs in the Actions graph;
- `firmware.yml` is the full image build, started after successful `main` CI,
  weekly, manually, or by a gated release-tag CI run; and
- `dependabot-automerge.yml` queues trusted Dependabot updates for squash merge
  after branch protection reports every required check green.

Workflows invoke the same package-local `justfile` capabilities used by
developers. Workflow YAML contains only scheduling, caching, artifact,
permission, and release policy.

`hardware.yml` runs PCB review followed by CAD checks in one `PCB → CAD` job.
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
