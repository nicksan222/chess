"""Fingerprints for the CAD sources and every published review artifact."""

import hashlib
import json
from pathlib import Path
from typing import cast

HARDWARE = Path(__file__).resolve().parents[3]


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_digest() -> str:
    digest = hashlib.sha256()
    for root in (HARDWARE / "cad", HARDWARE / "shared"):
        for path in sorted(root.rglob("*.py")):
            relative = path.relative_to(HARDWARE)
            if (
                "generated" in relative.parts
                or "tests" in relative.parts
                or path.name.startswith("test_")
                or path.name.endswith("_test.py")
            ):
                continue
            digest.update(str(relative).encode())
            digest.update(path.read_bytes())
    for path in (
        HARDWARE / "cad/justfile",
        HARDWARE / "build_support.py",
        HARDWARE.parent / ".devcontainer/Dockerfile",
        HARDWARE.parent / "pyproject.toml",
    ):
        if path.is_file():
            digest.update(str(path.relative_to(HARDWARE.parent)).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def record_provenance(directory: Path, manifest: dict[str, object]) -> None:
    manifest["source_digest"] = source_digest()
    manifest["artifact_sha256"] = {
        name: file_digest(directory / name)
        for name in cast(list[str], manifest["outputs"])
    }
    report = directory / "3d-models.json"
    if report.is_file():
        data = cast(dict[str, object], json.loads(report.read_text()))
        manifest["pcb_provenance"] = {
            key: data[key]
            for key in ("source_digest", "pcb_sha256", "glb_sha256", "snapshot_sha256")
        }


def artifacts_current(directory: Path) -> bool:
    try:
        manifest = cast(
            dict[str, object], json.loads((directory / "manifest.json").read_text())
        )
        outputs = cast(list[str], manifest["outputs"])
        hashes = cast(dict[str, str], manifest["artifact_sha256"])
        report_path = directory / "3d-models.json"
        if report_path.is_file():
            from .pcb_export import pcb_bundle_current

            report = cast(dict[str, object], json.loads(report_path.read_text()))
            expected = {
                key: report[key]
                for key in (
                    "source_digest",
                    "pcb_sha256",
                    "glb_sha256",
                    "snapshot_sha256",
                )
            }
            if (
                not pcb_bundle_current(directory)
                or manifest.get("pcb_provenance") != expected
            ):
                return False
        return (
            manifest.get("checks_passed") is True
            and manifest["source_digest"] == source_digest()
            and bool(outputs)
            and set(hashes) == set(outputs)
            and all(
                Path(name).name == name
                and file_digest(directory / name) == hashes[name]
                for name in outputs
            )
        )
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        return False
