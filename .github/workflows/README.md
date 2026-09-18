# Workflows

This directory owns GitHub Actions workflow definitions:

- `ci.yml` runs Hardware, Quality, and Pi harness on `main` and `v*` tags, and
  calls `firmware.yml` with publish enabled only for release tags;
- `pr.yml` runs those same checks on pull requests, plus Firmware checks
  (Yocto metadata and the AArch64 binary), posts one updated CI change report
  with semantic PCB component, wiring, placement, rule, and copper differences,
  and provides the `Required checks` branch-protection gate;
- `hardware.yml`, `quality.yml`, and `firmware-check.yml` are reusable domain
  workflows that group those jobs in the Actions graph;
- `firmware.yml` is the full image build, started after successful `main` CI,
  weekly, manually, or by a gated release-tag CI run; and
- `dependabot-automerge.yml` queues trusted Dependabot updates for squash merge
  after branch protection reports every required check green.

Workflows invoke the same package-local `justfile` capabilities used by
developers. Workflow YAML contains only scheduling, caching, artifact,
permission, and release policy.

PR reports compare freshly generated PCB output with the pull request's base
commit. They include ERC/DRC results and links to complete generated artifacts;
physical measurements remain a separate release requirement. GitHub withholds
write tokens from forked pull requests, so those runs keep the normal hardware
artifacts without attempting to post a comment.
