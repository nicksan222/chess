#!/usr/bin/env python3
"""Verify that Yocto can fetch every crates.io package in Cargo.lock."""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
LOCKFILE = ROOT / "Cargo.lock"
RECIPE = (
    ROOT / "apps/firmware/yocto/meta-firmware/recipes-firmware/firmware/firmware.bb"
)


def main() -> None:
    locked = tomllib.loads(LOCKFILE.read_text())["package"]
    packages_by_name: dict[str, list[dict[str, object]]] = {}
    for package in locked:
        packages_by_name.setdefault(package["name"], []).append(package)

    def resolve(dependency: str) -> dict[str, object]:
        name, *details = dependency.split()
        candidates = packages_by_name[name]
        if details and details[0][0].isdigit():
            candidates = [
                package for package in candidates if package["version"] == details[0]
            ]
        if len(candidates) != 1:
            raise ValueError(f"cannot resolve Cargo.lock dependency {dependency!r}")
        return candidates[0]

    root = next(package for package in locked if package["name"] == "firmware")
    pending = [root]
    visited: set[tuple[str, str, str]] = set()
    packages: dict[tuple[str, str], str] = {}
    while pending:
        package = pending.pop()
        identity = (
            package["name"],
            package["version"],
            package.get("source", ""),
        )
        if identity in visited:
            continue
        visited.add(identity)
        pending.extend(
            resolve(dependency) for dependency in package.get("dependencies", [])
        )
        if package.get("source", "").startswith("registry+"):
            packages[(package["name"], package["version"])] = package["checksum"]

    recipe = RECIPE.read_text()
    sources = set(re.findall(r"crate://crates\.io/([^/\s]+)/([^\s\\]+)", recipe))
    checksums = dict(
        re.findall(r'SRC_URI\[([^]]+)\.sha256sum\] = "([0-9a-f]{64})"', recipe)
    )

    errors: list[str] = []
    for name, version in sorted(packages.keys() - sources):
        errors.append(f"missing crate source: crate://crates.io/{name}/{version}")
    for name, version in sorted(sources - packages.keys()):
        errors.append(f"stale crate source: crate://crates.io/{name}/{version}")
    for (name, version), expected in sorted(packages.items()):
        key = f"{name}-{version}"
        actual = checksums.get(key)
        if actual != expected:
            errors.append(
                f"wrong checksum for {key}: expected {expected}, found {actual or 'none'}"
            )

    if errors:
        print("firmware Yocto crate metadata is stale:", file=sys.stderr)
        for error in errors:
            print(f"  - {error}", file=sys.stderr)
        raise SystemExit(1)


if __name__ == "__main__":
    main()
