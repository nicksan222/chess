# Project Pi harness

Project-local Pi extensions are intentionally split by responsibility:

- `auto-worktree` creates and switches to a unique `pi/<session-id>` Git
  worktree when a new Pi process starts;
- `change-tracker` attributes files changed during an agent turn to explicit
  edit/write calls, with snapshot fallback for shell-only mutation turns;
- `commit-loop` stages each planned tiny commit for interactive review, validates
  accepted patches, and resumes automatically after requested repair turns;
- `auto-validation` runs bounded fast validation after changed turns and gives
  failures back to the agent for at most two repair rounds;
- `verify-changes` provides the `verify_changes` tool and `/verify` command;
- `validation-status` owns only footer and editor-widget feedback;
- `pr-workflow` provides a standalone `/pr` pipeline that plans semantic commits,
  performs Git mutations, validates, pushes, and opens the pull request.

The extensions communicate through `pi.events`; common validation routing and
result formatting live in `feedback/verification.ts`.

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
to commit, request changes, or stop. Requested changes are safely unstaged and
handed back to the agent before the loop resumes automatically.

`/pr` uses the active model once to
produce a typed plan, then the extension itself creates or renames the branch,
creates ordered path-scoped commits, runs full validation, pushes, and invokes
`gh pr create`. It shows one complete plan and asks for confirmation before any
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
