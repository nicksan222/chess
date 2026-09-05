# Project Pi harness

Project-local Pi extensions are intentionally split by responsibility:

- `auto-worktree` creates and switches to a unique `pi/<session-id>` Git
  worktree when a new Pi process starts;
- `change-tracker` combines filesystem snapshots with commits created during a
  turn, while recording explicit edit/write paths as attribution metadata;
- `commit-loop` stages each planned tiny commit for interactive review, validates
  the exact staged snapshot, and resumes automatically after requested repairs;
- `auto-validation` runs bounded fast validation after changed turns and gives
  failures back to the agent for at most two repair rounds;
- `verify-changes` provides the `verify_changes` tool and `/verify` command;
- `validation-status` owns only footer and editor-widget feedback;
- `pr-workflow` provides a standalone `/pr` pipeline that plans semantic commits,
  performs Git mutations, validates, pushes, and opens the pull request.

The extensions communicate through `pi.events`; common validation routing and
result formatting live in `feedback/verification.ts`. Fast checks stay scoped,
while full validation also runs the repository precommit gate so reverse
package dependents are covered.

## Commands

```text
/verify [fast|test|full]
/validation-clear
/commit-loop [goal]
/pr [goal]
/worktree
```

`/worktree` is supplied by the installed `@narumitw/pi-worktree` package for
manual inspection, switching, and cleanup. `/commit-loop` uses the active model
to propose ordered path-scoped commits, stages one at a time, and asks whether
to commit, request changes, or stop. Each accepted patch is checked in a
temporary worktree containing only `HEAD` plus the staged snapshot. Requested
changes are safely unstaged and handed back to the agent before the loop resumes.

`/pr` scans both existing branch commits and the complete dirty patch for likely
secrets before sending anything to the active planning model. The extension then
creates or renames the branch, creates ordered path-scoped commits, validates a
clean committed snapshot, pushes, and invokes `gh pr create`. Existing branch
commits and newly planned commits are both shown in one confirmation before any
Git mutation or remote action.

## Automatic worktrees

The default root is `~/.worktrees`. Override it with
`PI_AUTO_WORKTREE_ROOT=/absolute/path` (or a `~/...` path). Set
`PI_AUTO_WORKTREE_DISABLE=1` for diagnostics or automation that must remain in
the launch directory. A failed setup leaves any successfully created worktree
in place for inspection; use `/worktree` to manage it safely.

Automatic worktrees begin at the launch worktree's committed `HEAD`. Uncommitted
launch-worktree changes are deliberately not copied into the isolated worktree.

## TypeScript development

The devcontainer installs Bun and VS Code uses the workspace TypeScript SDK from
`.pi/node_modules`. Dependencies and the lockfile are committed.

```sh
bun install --cwd .pi --frozen-lockfile
bun run --cwd .pi check
```

The check command runs strict TypeScript checking and the Bun test suite.
