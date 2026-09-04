# Workflows

This directory owns GitHub Actions workflow definitions:

- `ci.yml` runs the required pull request and main-branch checks;
- `firmware.yml` builds images manually, weekly, and for release tags; and
- `dependabot-automerge.yml` queues trusted Dependabot updates for squash merge
  after branch protection reports every required check green.

Workflows invoke the same package-local `justfile` capabilities used by
developers. Workflow YAML contains only scheduling, caching, artifact,
permission, and release policy.
