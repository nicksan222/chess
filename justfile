set shell := ["bash", "-euo", "pipefail", "-c"]

rust_packages := "apps/firmware crates/chess crates/core crates/logger crates/menu crates/persistence"
python_packages := "hardware/shared hardware/cad hardware/pcb"

# Show repository capabilities.
default:
    @just --list

# Complete repository validation and generation.
check: _automation-format agents-check
    #!/usr/bin/env bash
    set -euo pipefail
    for package in {{ rust_packages }}; do just --justfile "$package/justfile" check; done
    just firmware-binary
    just --justfile hardware/shared/justfile check
    just --justfile hardware/cad/justfile check
    just --justfile hardware/pcb/justfile review

# Commit gate without CAD renders or PCB fabrication output.
precommit: _automation-format agents-check
    #!/usr/bin/env bash
    set -euo pipefail
    for package in {{ rust_packages }}; do just --justfile "$package/justfile" check; done
    just firmware-binary
    just --justfile hardware/shared/justfile check
    just --justfile hardware/cad/justfile check-fast
    just --justfile hardware/pcb/justfile review

# Formatting, linting, checking, and documentation.
quality: _automation-format agents-check
    #!/usr/bin/env bash
    set -euo pipefail
    for package in {{ rust_packages }}; do just --justfile "$package/justfile" quality; done
    for package in {{ python_packages }}; do just --justfile "$package/justfile" quality; done

# Verify every package-owned justfile uses the canonical format.
[private]
_automation-format:
    #!/usr/bin/env bash
    set -euo pipefail
    files=(justfile)
    for package in {{ rust_packages }} {{ python_packages }}; do files+=("$package/justfile"); done
    for file in "${files[@]}"; do
        just --unstable --justfile "$file" --fmt --check
    done

# All package tests, including hardware validation.
test: agents-test
    #!/usr/bin/env bash
    set -euo pipefail
    for package in {{ rust_packages }}; do just --justfile "$package/justfile" test; done
    just --justfile hardware/shared/justfile test
    just --justfile hardware/cad/justfile test
    just --justfile hardware/pcb/justfile review

# Regenerate CAD and PCB review output.
generate:
    just --justfile hardware/cad/justfile generate
    just --justfile hardware/pcb/justfile review

# Regenerate CAD models and renders.
cad:
    just --justfile hardware/cad/justfile check

# Validate the PCB and regenerate its review output.
pcb:
    just --justfile hardware/pcb/justfile review

# Enforce physical release evidence and export PCB fabrication output.
pcb-release:
    just --justfile hardware/pcb/justfile release

# Compile and link the complete firmware crate graph for AArch64.
firmware-binary:
    just --justfile apps/firmware/justfile cross-build

# Regenerate Yocto crate metadata from the firmware Cargo.lock.
firmware-update-crates:
    just --justfile apps/firmware/justfile update-crates

# Validate the complete Yocto configuration.
firmware-check:
    just --justfile apps/firmware/justfile image-check

# Build the flashable Yocto image.
firmware:
    just --justfile apps/firmware/justfile image

# Configure runtime Herdr hooks and the pinned review panel (no model calls).
agents-setup:
    python3 .agents/team/setup.py

# Start missing team roles (asks Claude Code or Pi); accepts role selectors and flags.
[positional-arguments]
agents *args:
    python3 .agents/team/agents.py up "$@"

# Stop only this team's workspace or selected roles.
[positional-arguments]
agents-stop *args:
    python3 .agents/team/agents.py down "$@"

# Start fresh conversations and clear the session handoff.
[positional-arguments]
agents-reset *args:
    python3 .agents/team/agents.py reset "$@"

# Check container tools and provider login without a model request.
[positional-arguments]
agents-doctor *args:
    python3 .agents/team/agents.py doctor "$@"

# Show all configured models, harnesses and roles without starting them.
agents-list:
    python3 .agents/team/agents.py list

# Report local recorded Claude tokens, not remaining subscription allowance.
[positional-arguments]
agents-usage *args:
    python3 .agents/team/usage.py "$@"

# Lint, format-check and test agent tooling without provider/model requests.
agents-check:
    ruff check .agents/team
    ruff format --check .agents/team
    just agents-test

# Offline regressions; optional native smoke tests use HERDR_TEST_BIN.
agents-test:
    python3 -m unittest discover -s .agents/team/tests -v

# Remove package-local caches and transient output.
clean:
    #!/usr/bin/env bash
    set -euo pipefail
    for package in {{ rust_packages }}; do just --justfile "$package/justfile" clean; done
    for package in {{ python_packages }}; do just --justfile "$package/justfile" clean; done
