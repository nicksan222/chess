"""Headless Blender execution and atomic artifact publication."""

from __future__ import annotations

import json
import shutil
import subprocess
from collections.abc import Callable
from pathlib import Path
from typing import TypedDict, cast

from build_support import staged_output

from .provenance import artifacts_current, source_digest


class BlenderIdentity(TypedDict):
    version: str
    build_hash: str


def blender_identity(
    blender: Path,
    runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
) -> BlenderIdentity:
    """Read the version and build hash reported by the selected executable."""
    result = runner(
        [str(blender), "--version"], check=True, capture_output=True, text=True
    )
    lines = result.stdout.splitlines()
    first_line = lines[0] if lines else ""
    prefix = "Blender "
    if not first_line.startswith(prefix) or not first_line.removeprefix(prefix).strip():
        raise RuntimeError(f"Blender version output is invalid: {first_line!r}")
    build_prefix = "build hash:"
    build_hash = next(
        (
            line.strip().removeprefix(build_prefix).strip()
            for line in lines[1:]
            if line.strip().startswith(build_prefix)
        ),
        "",
    )
    if not build_hash:
        raise RuntimeError("Blender version output is missing the build hash")
    return {
        "version": first_line.removeprefix(prefix).strip(),
        "build_hash": build_hash,
    }


def blender_command(
    blender: Path,
    entry: Path,
    output: Path,
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
        str(entry),
        "--",
        str(output),
    ]
    # Forwarded host displays can hang EEVEE; use a private server when available.
    if find_executable("xvfb-run"):
        command = ["xvfb-run", "--auto-servernum", *command]
    return command


def publish(
    blender: Path,
    entry: Path,
    destination: Path,
    runner: Callable[..., object] = subprocess.run,
    prepare: Callable[[Path], None] | None = None,
    identity_reader: Callable[[Path], BlenderIdentity] = blender_identity,
) -> None:
    with staged_output(destination) as stage:
        if prepare is not None:
            prepare(stage)
        expected_identity = identity_reader(blender)
        expected_source = source_digest()
        runner(blender_command(blender, entry, stage), check=True)
        manifest_path = stage / "manifest.json"
        if not manifest_path.is_file():
            raise RuntimeError("CAD generation did not produce a manifest")
        manifest = cast(dict[str, object], json.loads(manifest_path.read_text()))
        runtime_value = manifest.get("blender_runtime")
        runtime = (
            cast(dict[str, object], runtime_value)
            if isinstance(runtime_value, dict)
            else {}
        )
        worker_identity: BlenderIdentity = {
            "version": cast(str, runtime.get("version", "")),
            "build_hash": cast(str, runtime.get("build_hash", "")),
        }
        if worker_identity != expected_identity:
            raise RuntimeError(
                "CAD worker runtime does not match the selected Blender executable"
            )
        outputs = cast(list[str], manifest["outputs"])
        if manifest.get("checks_passed") is not True or not outputs:
            raise RuntimeError("CAD generation checks are incomplete")
        for name in outputs:
            if (
                Path(name).name != name
                or not (stage / name).is_file()
                or not (stage / name).stat().st_size
            ):
                raise RuntimeError(f"CAD generation is missing output: {name}")
        if manifest.get("source_digest") != expected_source or not artifacts_current(
            stage
        ):
            raise RuntimeError("CAD artifact provenance is incomplete or stale")
    print(f"CAD: published {destination}")
