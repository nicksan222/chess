#!/usr/bin/env bash
# Exercise changed-scope routing in disposable repositories, including merge-base behavior.
set -euo pipefail
classifier="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)/changed-scopes.sh"
fixture=$(mktemp -d)
trap 'rm -rf "$fixture"' EXIT
cd "$fixture"
git init --quiet
git config user.email scopes-test@example.invalid
git config user.name scopes-test
git commit --quiet --allow-empty -m base
base=$(git rev-parse HEAD)
cases=0

check_scope() {
    local path=$1 expected=$2 result
    mkdir -p "$(dirname "$path")"
    printf 'fixture\n' > "$path"
    git add -- "$path"
    git commit --quiet -m fixture
    result=$(bash "$classifier" "$base" HEAD)
    [[ "$result" == "$expected" ]] || {
        printf 'Unexpected scopes for %s:\n%s\n' "$path" "$result" >&2
        exit 1
    }
    base=$(git rev-parse HEAD)
    cases=$((cases + 1))
}

result=$(bash "$classifier" "$base" "$base")
[[ "$result" == $'pcb=false\ncad=false\nhardware=false\nrust=false\nquality=false' ]]
cases=$((cases + 1))

check_scope docs/example.md $'pcb=false\ncad=false\nhardware=false\nrust=false\nquality=false'
check_scope .agents/roles/example.md $'pcb=false\ncad=false\nhardware=false\nrust=false\nquality=false'
check_scope crates/chess/src/example.rs $'pcb=false\ncad=false\nhardware=false\nrust=true\nquality=false'
check_scope rust-toolchain.toml $'pcb=false\ncad=false\nhardware=false\nrust=true\nquality=false'
check_scope hardware/pcb/example.py $'pcb=true\ncad=false\nhardware=true\nrust=false\nquality=false'
check_scope hardware/cad/example.py $'pcb=false\ncad=true\nhardware=true\nrust=false\nquality=false'
check_scope hardware/shared/example.py $'pcb=true\ncad=true\nhardware=true\nrust=false\nquality=false'
check_scope tooling/quality/justfile $'pcb=false\ncad=false\nhardware=false\nrust=false\nquality=true'
check_scope pyproject.toml $'pcb=true\ncad=true\nhardware=true\nrust=false\nquality=false'
check_scope unknown/config $'pcb=true\ncad=true\nhardware=true\nrust=true\nquality=true'

check_scope $'hardware/cad/odd\nname.py' $'pcb=false\ncad=true\nhardware=true\nrust=false\nquality=false'

# An unrelated change on the base branch must not expand a documentation-only PR.
git checkout --quiet -b topic
check_scope docs/topic.md $'pcb=false\ncad=false\nhardware=false\nrust=false\nquality=false'
head=$(git rev-parse HEAD)
git checkout --quiet --detach HEAD~1
printf 'base-only\n' > justfile
git add justfile
git commit --quiet -m base-only
result=$(bash "$classifier" HEAD "$head")
[[ "$result" == $'pcb=false\ncad=false\nhardware=false\nrust=false\nquality=false' ]]
cases=$((cases + 1))
# Failed input must fail the job rather than silently report every scope false.
if bash "$classifier" invalid-revision "$head" > invalid-output 2>/dev/null; then
    printf 'Invalid revisions incorrectly succeeded\n' >&2
    exit 1
fi
[[ ! -s invalid-output ]]
cases=$((cases + 1))
printf 'Changed-scope routing: %d cases passed\n' "$cases"
