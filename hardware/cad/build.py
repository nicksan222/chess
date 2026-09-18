"""Generate and atomically publish the complete CAD artifact set."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
from collections.abc import Callable, Mapping
from pathlib import Path

from build_support import staged_output

CAD_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = CAD_ROOT.parents[1]
PROJECTS = CAD_ROOT / "projects"
GENERATED = CAD_ROOT / "generated"
GENERATED_README = GENERATED / "README.md"


def ordered_generators(projects: Path = PROJECTS) -> list[Path]:
    """Discover generators in their declared dependency order."""
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
    environment: Mapping[str, str] = os.environ,
    find_executable: Callable[[str], str | None] = shutil.which,
) -> list[str]:
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
    if not environment.get("DISPLAY") and find_executable("xvfb-run"):
        command = ["xvfb-run", "--auto-servernum", *command]
    return command


def generate(
    blender: Path,
    destination: Path = GENERATED,
    runner: Callable[..., object] = subprocess.run,
) -> None:
    """Build every project into one stage, then publish the whole set."""
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
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("blender", type=Path)
    args = parser.parse_args()
    generate(args.blender)


if __name__ == "__main__":
    main()
