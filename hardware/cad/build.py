"""Generate and atomically publish the complete CAD artifact set.

Role: the driver behind `just --justfile hardware/cad/justfile generate`. It finds
every `projects/*/generate.py`, runs each in its own Blender process in dependency
order, and publishes all outputs together. Each generator writes into one shared
staging directory (via `build_support.staged_output`), which replaces `generated/`
only if every project succeeded, so a failed model or render never leaves a mixed
set. Usage (as the recipe runs it): `PYTHONPATH=hardware python3 -m cad.build <path-to-blender>`.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import cast

from build_support import staged_output

# Paths are derived from this file so the build works from any working directory.
CAD_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = CAD_ROOT.parents[1]
PROJECTS = CAD_ROOT / "projects"
GENERATED = CAD_ROOT / "generated"
# Hand-written note kept in `generated/`; copied into each new stage because the stage
# replaces the whole directory (and would otherwise delete it).
GENERATED_README = GENERATED / "README.md"


def ordered_generators(projects: Path = PROJECTS) -> list[Path]:
    """Discover generators in their declared dependency order.

    A project may contain a `generation-order` file holding a non-negative integer
    (default 100); lower numbers run first. This is how `board-assembly` runs after
    the parts it imports. Ties sort by path so the order is deterministic.
    """
    ranked: list[tuple[int, str, Path]] = []
    for generator in projects.glob("*/generate.py"):
        order_file = generator.parent / "generation-order"
        if order_file.is_file():
            order_lines = order_file.read_text().splitlines()
            order_text = order_lines[0] if order_lines else ""
        else:
            order_text = "100"
        try:
            order = int(order_text)
        except ValueError as error:
            raise RuntimeError(
                f"Invalid generation order in {order_file}: {order_text}"
            ) from error
        if order < 0:
            raise RuntimeError(
                f"Invalid generation order in {order_file}: {order_text}"
            )
        ranked.append((order, str(generator), generator))
    if not ranked:
        raise RuntimeError("no CAD project generators found")
    return [generator for _order, _name, generator in sorted(ranked)]


def generator_command(
    blender: Path,
    generator: Path,
    output_directory: Path,
    find_executable: Callable[[str], str | None] = shutil.which,
) -> list[str]:
    """Blender command for one generator (`find_executable` is injectable for tests).

    Renders always go through a private Xvfb server when one is available. An
    inherited DISPLAY is not trusted: a devcontainer forwards the host's X
    server, and EEVEE rendering through it hangs without reporting an error.
    """
    # `--python-exit-code 1` makes a script exception fail the build; `--gpu-backend
    # opengl` selects the backend EEVEE renders with in the background.
    command = [
        str(blender),
        "--background",
        "--factory-startup",
        "--gpu-backend",
        "opengl",
        "--python-exit-code",
        "1",
        "--python",
        str(generator),
        "--",
        str(output_directory),
    ]
    if find_executable("xvfb-run"):
        command = ["xvfb-run", "--auto-servernum", *command]
    return command


def generate(
    blender: Path,
    destination: Path = GENERATED,
    runner: Callable[..., object] = subprocess.run,
) -> None:
    """Build every project into one stage, then publish the whole set.

    `runner` is injectable (defaults to `subprocess.run`) so tests can check the
    sequence without launching Blender. `check=True` aborts on the first failure,
    which leaves the previously published set untouched.
    """
    with staged_output(destination) as stage:
        if GENERATED_README.is_file():
            shutil.copyfile(GENERATED_README, stage / GENERATED_README.name)
        for generator in ordered_generators():
            print(f"\n==> Generate {generator.parent.relative_to(REPOSITORY_ROOT)}")
            runner(
                generator_command(blender, generator, stage),
                cwd=REPOSITORY_ROOT,
                check=True,
            )
    print(f"CAD: published {destination}")


def main() -> None:
    """CLI entry: the only argument is the Blender executable to use."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("blender", type=Path)
    args = parser.parse_args()
    generate(cast(Path, args.blender))


if __name__ == "__main__":
    main()
