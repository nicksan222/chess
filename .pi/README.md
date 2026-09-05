# Project Pi setup

The project keeps two small local commands:

- `/commit-loop [goal]` plans, reviews, and creates sequential commits;
- `/pr [goal]` plans commits, creates a semantic branch, and opens a pull
  request with `gh`.

Both commands create ordinary Git commits. They do not bypass or duplicate
validation: every commit runs `.githooks/pre-commit`, which invokes
`just precommit`.

Worktrees are handled entirely by the installed
[`pi-worktrees`](https://pi.dev/packages/pi-worktrees?page=73) package:

```text
/wt
/wt create [name] [--move]
/wt return [--move]
/wt delete <path>
```

Managed worktrees use the package default at `~/.local/share/pi-worktrees`.
There is no project-specific worktree implementation.

## Development

```sh
bun install --cwd .pi --frozen-lockfile
bun run --cwd .pi check
```
