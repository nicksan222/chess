set shell := ["bash", "-euo", "pipefail", "-c"]

rust_packages := "apps/firmware crates/chess crates/core crates/logger crates/menu crates/persistence"
python_packages := "hardware/shared hardware/cad hardware/pcb"

# Show repository capabilities.
default:
    @just --list

# Complete repository validation and generation.
check: _automation-format
    #!/usr/bin/env bash
    set -euo pipefail
    for package in {{ rust_packages }}; do just --justfile "$package/justfile" check; done
    just firmware-binary
    just --justfile hardware/shared/justfile check
    just --justfile hardware/cad/justfile check
    just --justfile hardware/pcb/justfile review

# Commit gate without CAD renders or PCB fabrication output.
precommit: _automation-format
    #!/usr/bin/env bash
    set -euo pipefail
    for package in {{ rust_packages }}; do just --justfile "$package/justfile" check; done
    just firmware-binary
    just --justfile hardware/shared/justfile check
    just --justfile hardware/cad/justfile check-fast
    just --justfile hardware/pcb/justfile review

# Formatting, linting, checking, and documentation.
quality: _automation-format
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
test:
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
