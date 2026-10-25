# Quality tooling

Recipes for the repository rules that the compilers and package linters do not
cover, and for dependency health. Every rule is configuration for a maintained
tool; there is no checker code here. [`docs/development.md`](../../docs/development.md#quality-checks)
lists which tool enforces what across the repository.

```sh
just --justfile tooling/quality/justfile quality        # patterns, names, crate boundaries (offline)
just --justfile tooling/quality/justfile patterns       # ast-grep rule tests, then a scan
just --justfile tooling/quality/justfile dependencies   # cargo deny, cargo shear, pip-audit (network)
```

| Rule | Tool and configuration | Documented exceptions |
| --- | --- | --- |
| `no-hardcoded-timing`: firmware delays, intervals and timeouts live in `tuning!` | ast-grep, [`../ast-grep/rules/no-hardcoded-timing.yml`](../ast-grep/rules/no-hardcoded-timing.yml) | `src/tuning/`, `src/harness.rs` (test wait bounds) and test items; `CONNECT_TIMEOUT`, `REQUEST_TIMEOUT` and the preflight `PROBE` are network or D-Bus bounds marked with `// ast-grep-ignore: no-hardcoded-timing` and a reason |
| `pins-only-in-pins`: BCM/GPIO numbers only in `apps/firmware/src/hardware/pins.rs` | ast-grep, [`../ast-grep/rules/pins-only-in-pins.yml`](../ast-grep/rules/pins-only-in-pins.yml) | Test items |
| `no-todo-comments`: no TODO, FIXME, XXX or HACK markers in Rust comments (Ruff `FIX` covers Python); unfinished work is an issue | ast-grep, [`../ast-grep/rules/no-todo-comments.yml`](../ast-grep/rules/no-todo-comments.yml) | None |
| Crate boundaries: `crates/*` never reach `firmware`, `tokio`, `gpiocdev` or `nmrs`; internal dependencies only as listed | cargo-deny `[bans]`: `wrappers` in [`../../deny.toml`](../../deny.toml), and [`portable.deny.toml`](portable.deny.toml) run with each `crates/*` manifest as the sole root | None |
| File names: snake_case `.rs` and `.py` | ls-lint, [`../../.ls-lint.yml`](../../.ls-lint.yml) | Python `__init__`/`__main__`; generated, build and cache directories are ignored |
| Package layout: every `apps/*` and `crates/*` root holds exactly one `Cargo.toml` and one `README.md`; directories in Rust module trees and Python packages are snake_case | ls-lint, [`../../.ls-lint.yml`](../../.ls-lint.yml) | Yocto layers and `.github` keep their kebab-case names; the extensionless `justfile` cannot be matched |
| Shell scripts: `*.sh` and `.githooks/pre-commit` | ShellCheck (from the dev container's Ubuntu packages) | None |
| Yocto manifest sync | A plain test, `apps/firmware/tests/yocto_manifest.rs` | None |

## Adding a pattern rule

Add one ast-grep rule and its test; no code changes:

1. `tooling/ast-grep/rules/<id>.yml`: `id`, `language`, `severity: error`, a
   `message` and a `note` saying what to do instead, `files`/`ignores` globs, and
   the `rule` (patterns, `kind`, `regex`, `inside`/`not` relations and
   `constraints`). Exclude Rust test code with
   `not: { inside: { stopBy: end, any: [...] } }` as the existing rules do.
2. `tooling/ast-grep/rule-tests/<id>-test.yml`: `valid` snippets that must not
   report and `invalid` snippets that must, at least one each.
3. `just --justfile tooling/quality/justfile patterns`. The
   [ast-grep playground](https://ast-grep.github.io/playground.html) shows the
   syntax tree a pattern must match.

A deliberate exception is a comment saying why, then
`// ast-grep-ignore: <id>` on the line before the code (`# ast-grep-ignore:` in
Python). `ast-grep scan` honours it; `ast-grep test` does not, so tests do not
use it. A path-wide exception is an `ignores` glob with a comment.

Crate boundaries are `deny` entries in `deny.toml` (`wrappers` lists the crates
allowed to depend directly on the banned one) or entries in
`portable.deny.toml`. A `wrappers` list cannot say "no dependents" for a crate
that is itself a graph root: cargo-deny would ban the root. That is why the
application and its async stack are banned per portable crate instead.

## Not covered by a package

- Package conventions ls-lint cannot express (every package has a `justfile`,
  every package `justfile` is listed in the root `justfile`, every crate has a CI
  test job) are not enforced; the root `justfile` and
  `.github/workflows/README.md` document them.
- File length: Clippy (`too_many_lines`) and Ruff (`PLR0915`, `C90`) limit
  functions, not files.
- Physical number literals in `hardware/cad` and `hardware/pcb` outside
  `hardware/shared` (deferred). About a thousand literals match, most of them
  component footprint and pin geometry from datasheets, which the component
  module legitimately owns, and render settings. A precise rule needs an agreed
  list of the quantities that must come from `hardware/shared` first.

## Dependencies

| Tool | Checks | Configuration |
| --- | --- | --- |
| `cargo deny` | Advisories (vulnerable, unsound and yanked anywhere; unmaintained direct dependencies), MIT-compatible licences, bans and crate boundaries, wildcard versions, sources; duplicate versions warn | [`deny.toml`](../../deny.toml), run against `Cargo.lock` and `apps/firmware/yocto/Cargo.lock` |
| `cargo shear` | Unused and misplaced (should be `dev-`) Rust dependencies | `[package.metadata.cargo-shear]`, each entry with a comment |
| `pip-audit` | Known vulnerabilities in the pinned development-container Python tools | [`.devcontainer/requirements.txt`](../../.devcontainer/requirements.txt), `--no-deps`; vtk 9.3.1's advisories are ignored in the recipe because cadquery-ocp 7.8 pins it until a verified move to cadquery 2.8 |

`cargo shear` was chosen over `cargo machete` because it parses Rust sources
with rust-analyzer's parser instead of matching text, so renamed crates,
macros and `use` trees produce fewer false positives, and it also flags
dependencies only tests use. Like `machete`, it needs no compilation.

All tools are pinned in [`.devcontainer/`](../../.devcontainer/README.md); CI
runs these recipes in the prebuilt container.
