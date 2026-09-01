SHELL := /usr/bin/env bash
.DEFAULT_GOAL := help

PCB_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
ROOT := $(abspath $(PCB_DIR)/../..)
DEVCONTAINER ?= devcontainer
DOCKER ?= docker
DC := $(DEVCONTAINER) exec --workspace-folder "$(ROOT)"
CONTAINER_IDS = $(DOCKER) ps -aq --filter "label=devcontainer.local_folder=$(ROOT)"

.PHONY: help doctor build up shell exec test component-check bom schematic board \
	review release check clean stop down logs

help: ## Show the supported container-based PCB operations.
	@printf 'Usage: make -C hardware/pcb <target>\n\n'
	@printf 'Container lifecycle:\n'
	@grep -E '^(doctor|build|up|shell|exec|logs|stop|down):.*##' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*## "} {printf "  %-18s %s\n", $$1, $$2}'
	@printf '\nBoard operations (all run inside the dev container):\n'
	@grep -E '^(test|component-check|bom|schematic|board|review|release|check|clean):.*##' $(MAKEFILE_LIST) | \
		awk 'BEGIN {FS = ":.*## "} {printf "  %-18s %s\n", $$1, $$2}'

doctor: ## Verify Docker and the Dev Container CLI are usable.
	@command -v $(DOCKER) >/dev/null || { echo 'error: Docker is not installed' >&2; exit 1; }
	@$(DOCKER) info >/dev/null || { echo 'error: Docker daemon is unavailable' >&2; exit 1; }
	@command -v $(DEVCONTAINER) >/dev/null || { echo 'error: install @devcontainers/cli' >&2; exit 1; }
	@printf 'Docker and devcontainer are ready.\n'

build: doctor ## Build the reproducible KiCad 9 development image.
	cd "$(ROOT)" && $(DEVCONTAINER) build --workspace-folder "$(ROOT)"

up: doctor ## Build if needed and start the repository development container.
	cd "$(ROOT)" && $(DEVCONTAINER) up --workspace-folder "$(ROOT)"

shell: up ## Open a shell in the development container.
	cd "$(ROOT)" && $(DC) bash

exec: up ## Run CMD in the container, e.g. make exec CMD='kicad-cli version'.
	@test -n "$(CMD)" || { echo "error: CMD is required" >&2; exit 2; }
	cd "$(ROOT)" && $(DC) bash -lc '$(CMD)'

test: up ## Run fast PCB composition, component, footprint, and placement tests.
	cd "$(ROOT)" && $(DC) env PYTHONPATH=hardware:hardware/pcb \
		python3 -m unittest discover -s hardware/pcb/tests -p 'test_*.py'

component-check: up ## Prove every BOM product, semantic pin, and footprint agree.
	cd "$(ROOT)" && $(DC) env PYTHONPATH=hardware:hardware/pcb \
		python3 -m unittest hardware.pcb.tests.test_components \
		hardware.pcb.tests.test_footprints hardware.pcb.tests.test_release_policy

bom: up ## Regenerate the exact-manufacturer-part-number BOM.
	cd "$(ROOT)" && $(DC) python3 hardware/pcb/write_bom.py

schematic: up ## Regenerate the native KiCad schematic and symbol library.
	cd "$(ROOT)" && $(DC) python3 hardware/pcb/write_schematic.py

board: up ## Regenerate the schematic, PCB, BOM, and KiCad project configuration.
	cd "$(ROOT)" && $(DC) bash -lc \
		'python3 hardware/pcb/write_bom.py && \
		 python3 hardware/pcb/write_schematic.py && \
		 python3 hardware/pcb/generate.py && \
		 python3 hardware/pcb/configure_project.py'

review: up ## Run generation, tests, ERC, DRC, parity, and renders without Gerbers.
	cd "$(ROOT)" && $(DC) env PCB_REVIEW_ONLY=1 ./tools/pcb

release: up ## Run every gate and export fabrication files only if release-ready.
	cd "$(ROOT)" && $(DC) ./tools/pcb

check: up ## Run the complete Rust, CAD, and PCB repository check.
	cd "$(ROOT)" && $(DC) ./tools/check

clean: up ## Remove Python caches and stale fabrication output, preserving reviews.
	cd "$(ROOT)" && $(DC) bash -lc \
		'find hardware/pcb -type d -name __pycache__ -prune -exec rm -rf {} +; \
		 rm -f hardware/pcb/generated/*.kicad_prl hardware/pcb/generated/~*.lck; \
		 rm -rf hardware/pcb/generated/gerber'

logs: doctor ## Follow output from the active development container.
	@ids="$$($(CONTAINER_IDS))"; test -n "$$ids" || { echo 'error: container is not running' >&2; exit 1; }; \
	$(DOCKER) logs -f $$(printf '%s\n' "$$ids" | head -n1)

stop: doctor ## Stop the repository development container.
	@$(CONTAINER_IDS) | xargs -r $(DOCKER) stop

down: doctor ## Remove the repository development container (the image is retained).
	@$(CONTAINER_IDS) | xargs -r $(DOCKER) rm -f
