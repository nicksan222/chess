# Workflows

This directory owns GitHub Actions workflow definitions:

- `ci.yml` runs required pull request and main-branch checks, cross-compiles and
  links the complete firmware crate graph for AArch64, and gates release tags;
- `firmware.yml` is the reusable full image build invoked manually, weekly, or
  by a successful release-tag CI run; and
- `dependabot-automerge.yml` queues trusted Dependabot updates for squash merge
  after branch protection reports every required check green.

Workflows invoke the same package-local `justfile` capabilities used by
developers. Workflow YAML contains only scheduling, caching, artifact,
permission, and release policy.
