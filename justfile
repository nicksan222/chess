set shell := ["bash", "-euo", "pipefail", "-c"]

rust_packages := "apps/firmware crates/chess crates/core crates/logger crates/menu crates/persistence"
python_packages := "hardware/shared hardware/cad hardware/pcb"

# Show repository capabilities.
default:
    @just --list

# Show the on-demand development tool overview.
welcome:
    @bash .devcontainer/welcome.sh

# Complete repository validation and generation.
check: _automation-format
    #!/usr/bin/env bash
    set -euo pipefail
    for package in {{ rust_packages }}; do just --justfile "$package/justfile" check; done
    just firmware-binary
    just --justfile hardware/shared/justfile check
    just --justfile hardware/pcb/justfile review
    just --justfile hardware/cad/justfile quality test generate
    just --justfile tooling/quality/justfile check

# Fast commit gate: lint and tests; no renders, PCB regeneration or cross-build (CI runs them).
precommit: _automation-format
    #!/usr/bin/env bash
    set -euo pipefail
    for package in {{ rust_packages }}; do just --justfile "$package/justfile" check; done
    just --justfile hardware/shared/justfile check
    just --justfile hardware/cad/justfile quality test
    just --justfile hardware/pcb/justfile check
    just --justfile tooling/quality/justfile quality

# Formatting, linting, documentation, patterns and crate boundaries.

# Set hardware=false only when a companion hardware workflow owns Python quality.
quality hardware="true": _automation-format
    #!/usr/bin/env bash
    set -euo pipefail
    for package in {{ rust_packages }}; do just --justfile "$package/justfile" quality; done
    if [[ "{{ hardware }}" == true ]]; then
        for package in {{ python_packages }}; do just --justfile "$package/justfile" quality; done
    fi
    just --justfile tooling/quality/justfile quality

# Verify every package-owned justfile uses the canonical format.
[private]
_automation-format:
    #!/usr/bin/env bash
    set -euo pipefail
    files=(justfile tooling/quality/justfile)
    for package in {{ rust_packages }} {{ python_packages }}; do files+=("$package/justfile"); done
    for file in "${files[@]}"; do
        just --unstable --justfile "$file" --fmt --check
    done

# Run every Rust test target with one shared compilation graph.
rust-test:
    cargo test --locked --workspace --all-targets --all-features

# All package tests, including hardware validation.
test:
    #!/usr/bin/env bash
    set -euo pipefail
    for package in {{ rust_packages }}; do just --justfile "$package/justfile" test; done
    just --justfile hardware/shared/justfile test
    just --justfile hardware/cad/justfile test
    just --justfile hardware/pcb/justfile review
    just --justfile tooling/quality/justfile patterns

# Advisories, licences, bans and unused dependencies; needs network access.
dependencies:
    just --justfile tooling/quality/justfile dependencies

# Regenerate CAD and PCB review output.
generate:
    just --justfile hardware/pcb/justfile review
    just --justfile hardware/cad/justfile generate

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

# Remove package-local caches and transient output.
clean:
    #!/usr/bin/env bash
    set -euo pipefail
    for package in {{ rust_packages }}; do just --justfile "$package/justfile" clean; done
    for package in {{ python_packages }}; do just --justfile "$package/justfile" clean; done
