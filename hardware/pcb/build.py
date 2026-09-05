"""One build pipeline; reviewed outputs are published only as complete sets."""

from __future__ import annotations

import fcntl
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Generator, Mapping
from contextlib import contextmanager
from pathlib import Path
from typing import TypeGuard, cast

import pcbnew

from pcb.definition import board as definition
from pcb.definition.native import ORIGIN_X_MM, ORIGIN_Y_MM, connections, parts

PCB_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = PCB_ROOT.parents[1]
GENERATED_DIR = Path(os.environ.get("PCB_OUTPUT", PCB_ROOT / "generated"))
BOARD = GENERATED_DIR / "chess-board.kicad_pcb"
DSN = GENERATED_DIR / "chess-board.dsn"
PROJECT = GENERATED_DIR / "chess-board.kicad_pro"
SCHEMATIC = GENERATED_DIR / "chess-board.kicad_sch"
SYMBOL_LIBRARY = GENERATED_DIR / "generated-symbols.kicad_sym"
SYMBOL_TABLE = GENERATED_DIR / "sym-lib-table"
BOM = GENERATED_DIR / "bom.md"
ASSEMBLY_BOM = GENERATED_DIR / "assembly-bom.csv"
BOARD_TOP_SVG = GENERATED_DIR / "board-top.svg"
BOARD_BOTTOM_SVG = GENERATED_DIR / "board-bottom.svg"


def run(
    *args: str, output: Path | None = None, env: dict[str, str] | None = None
) -> str:
    result = subprocess.run(
        args, cwd=REPOSITORY_ROOT, env=env, capture_output=True, text=True, check=False
    )
    text = result.stdout + result.stderr
    if output is not None:
        output.write_text(text)
    if result.returncode:
        raise RuntimeError(
            f"{' '.join(args)} failed ({result.returncode})\n{text[-12000:]}"
        )
    return text.strip()


def doctor(*, simulation: bool) -> dict[str, str]:
    for executable in ("kicad-cli", "ngspice") if simulation else ("kicad-cli",):
        if shutil.which(executable) is None:
            raise RuntimeError(f"{executable} is required")
    import pcbnew

    version = pcbnew.GetBuildVersion()
    if not version.startswith("9."):
        raise RuntimeError(f"KiCad 9 is required, found {version}")
    tools = {
        "python": sys.version.split()[0],
        "pcbnew": version,
        "kicad-cli": run("kicad-cli", "--version"),
    }
    if simulation:
        tools["ngspice"] = run("ngspice", "--version")
    return tools


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_hashes() -> dict[str, str]:
    roots = (PCB_ROOT, PCB_ROOT.parent / "shared")
    files = [
        p
        for root in roots
        for p in root.rglob("*")
        if p.is_file()
        and p.suffix in {".py", ".pyi", ".json"}
        and not {"generated", "__pycache__"}.intersection(p.parts)
    ]
    files.extend((PCB_ROOT / "justfile", REPOSITORY_ROOT / "pyproject.toml"))
    return {str(p.relative_to(REPOSITORY_ROOT)): digest(p) for p in sorted(files)}


@contextmanager
def staged_output(destination: Path) -> Generator[Path]:
    """No generator writes into reviewed output. Roll back publication failures.

    Directory renames expose only whole sets, never a mixture of old and new files.
    The advisory lock serializes writers, without exposing partial builds.
    """
    destination.parent.mkdir(parents=True, exist_ok=True)
    lock_path = Path(tempfile.gettempdir()) / (
        "chess-pcb-"
        + hashlib.sha256(str(destination.resolve()).encode()).hexdigest()[:16]
        + ".lock"
    )
    with lock_path.open("w") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        with tempfile.TemporaryDirectory(
            prefix=".pcb-build-", dir=destination.parent
        ) as temporary:
            stage = Path(temporary) / "generated"
            stage.mkdir()
            yield stage
            backup = Path(temporary) / "previous"
            if destination.exists():
                destination.rename(backup)
            try:
                stage.rename(destination)
            except BaseException:
                if backup.exists():
                    backup.rename(destination)
                raise


def generate(design: pcbnew.BOARD, out: Path) -> None:
    from pcb.definition import native
    from pcb.definition.output import exports, schematic
    from pcb.definition.routing import policies as routing

    (out / PROJECT.name).write_text(exports.render_project())
    (out / BOM.name).write_text(exports.render_bom(design))
    (out / ASSEMBLY_BOM.name).write_text(exports.render_assembly_csv(design))
    (out / "netlist.json").write_text(
        json.dumps(
            {"schema": 1, "projects": {"board": definition.netlist(design)}},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    schematic.write(design, out)
    routing.route(design)
    native.add_power_planes(design)
    native.write_board(design, out / BOARD.name, out / DSN.name)
    # pcbnew writes defaults beside the board while filling; reviewed settings win.
    (out / PROJECT.name).write_text(exports.render_project())


def native_checks(out: Path) -> None:
    run(
        "kicad-cli",
        "sch",
        "erc",
        "--severity-all",
        "--format",
        "json",
        "-o",
        str(out / "erc.json"),
        str(out / SCHEMATIC.name),
    )
    run(
        "kicad-cli",
        "pcb",
        "drc",
        "--schematic-parity",
        "--severity-all",
        "--severity-exclusions",
        "--format",
        "json",
        "-o",
        str(out / "drc.json"),
        str(out / BOARD.name),
    )
    run(
        "kicad-cli",
        "pcb",
        "drc",
        "--schematic-parity",
        "--severity-all",
        "--severity-exclusions",
        "-o",
        str(out / "drc.rpt"),
        str(out / BOARD.name),
    )
    erc = json.loads((out / "erc.json").read_text())
    drc = json.loads((out / "drc.json").read_text())
    if any(s["violations"] for s in erc["sheets"]) or any(
        drc[key] for key in ("violations", "unconnected_items", "schematic_parity")
    ):
        raise RuntimeError(
            f"native electrical/layout checks failed: ERC={erc}; DRC={drc}"
        )
    run(
        "kicad-cli",
        "pcb",
        "export",
        "pos",
        "--format",
        "csv",
        "--units",
        "mm",
        "--side",
        "both",
        "--exclude-dnp",
        "-o",
        str(out / "positions.csv"),
        str(out / BOARD.name),
    )


def tests(out: Path) -> None:
    env = dict(
        os.environ,
        PYTHONPATH=str(PCB_ROOT.parent),
        PCB_OUTPUT=str(out),
        PCB_SPICE_OUTPUT=str(out / "spice"),
    )
    run(
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        str(PCB_ROOT / "tests"),
        "-p",
        "test_*.py",
        env=env,
        output=out / "tests.log",
    )


def previews(out: Path) -> None:
    from pcb.definition.output.exports import polish

    run(
        "kicad-cli",
        "sch",
        "export",
        "svg",
        "--exclude-drawing-sheet",
        "--no-background-color",
        "-o",
        str(out / "schematic"),
        str(out / SCHEMATIC.name),
    )
    for side, layers in (
        ("top", "F.Cu,F.Mask,F.Silkscreen,Edge.Cuts"),
        ("bottom", "B.Cu,B.Mask,B.Silkscreen,Edge.Cuts"),
    ):
        path = out / f"board-{side}.svg"
        mirror = ("--mirror",) if side == "bottom" else ()
        run(
            "kicad-cli",
            "pcb",
            "export",
            "svg",
            "--mode-single",
            "--page-size-mode",
            "2",
            "--fit-page-to-board",
            "--exclude-drawing-sheet",
            "--subtract-soldermask",
            *mirror,
            "-l",
            layers,
            "-o",
            str(path),
            str(out / BOARD.name),
        )
        polish(path, side)
    for name, options in (
        (
            "3d",
            (
                "--width",
                "1800",
                "--height",
                "1200",
                "--floor",
                "--perspective",
                "--rotate",
                "325,0,35",
                "--zoom",
                "0.75",
            ),
        ),
        (
            "top",
            ("--width", "1400", "--height", "1400", "--side", "top", "--zoom", "0.82"),
        ),
        (
            "bottom",
            (
                "--width",
                "1400",
                "--height",
                "1400",
                "--side",
                "bottom",
                "--zoom",
                "0.82",
            ),
        ),
    ):
        run(
            "kicad-cli",
            "pcb",
            "render",
            "--quality",
            "high",
            "--background",
            "opaque",
            *options,
            "-o",
            str(out / f"board-{name}.png"),
            str(out / BOARD.name),
        )


def _measurement_list(value: object) -> TypeGuard[list[float | int]]:
    return isinstance(value, list) and all(
        _positive_number(v) for v in cast(list[object], value)
    )


def _positive_number(value: object) -> TypeGuard[int | float]:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0
    )


def physical_evidence(path: Path | None = None) -> None:
    """Human Hall/magnet measurements are a production release gate, not a test skip."""
    path = path or PCB_ROOT / "definition/evidence/hall-magnet.json"
    if not path.is_file():
        raise RuntimeError(f"missing physical evidence: {path}")
    record = object_fields(json.loads(path.read_text()))
    identity = {
        "schema": 1,
        "board_revision": "D-PROTOTYPE",
        "sensor_mpn": "DRV5032FCDBZR",
    }
    if any(record.get(key) != value for key, value in identity.items()):
        raise RuntimeError("Hall evidence identity fields are invalid")
    if record.get("pass") is not True:
        raise RuntimeError("Hall evidence must explicitly pass")
    final_gap = record.get("final_gap_mm")
    if not _positive_number(final_gap):
        raise RuntimeError("Hall evidence requires a positive final assembled gap")
    for pole in ("north", "south"):
        measurements = object_fields(record.get(pole))
        for name in ("operate_mm", "release_mm"):
            values = measurements.get(name)
            if not _measurement_list(values) or len(values) < 5:
                raise RuntimeError(
                    f"{pole}/{name}: require five positive measured distances"
                )
            if name == "operate_mm" and min(values) < final_gap + 0.5:
                raise RuntimeError(f"{pole}: less than 0.5 mm operating margin")
    notes = record.get("notes")
    if not isinstance(notes, str) or not notes.strip():
        raise RuntimeError("Hall evidence requires measurement notes")


def fabrication(out: Path) -> None:
    folder = out / "gerber"
    folder.mkdir()
    layers = "F.Cu,In1.Cu,In2.Cu,In3.Cu,In4.Cu,In5.Cu,In6.Cu,B.Cu,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,F.Mask,B.Mask,Edge.Cuts"
    run(
        "kicad-cli",
        "pcb",
        "export",
        "gerbers",
        "-l",
        layers,
        "-o",
        str(folder) + "/",
        str(out / BOARD.name),
    )
    run(
        "kicad-cli",
        "pcb",
        "export",
        "drill",
        "--excellon-separate-th",
        "--excellon-oval-format",
        "route",
        "--generate-report",
        "--report-path",
        str(folder / "drill-report.rpt"),
        "-o",
        str(folder) + "/",
        str(out / BOARD.name),
    )


def check() -> None:
    """Non-publishing native-definition/dimensions checks; review also checks copper."""
    definition.load()
    run("ruff", "check", str(PCB_ROOT))
    run("ruff", "format", "--check", str(PCB_ROOT))
    analyzer = os.environ.get("PYRIGHT", "pyright")
    run(analyzer, "--project", str(PCB_ROOT / "pyrightconfig.json"))
    env = dict(os.environ, PYTHONPATH=str(PCB_ROOT.parent))
    run(
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        str(PCB_ROOT / "tests"),
        "-p",
        "test_dimensions.py",
        env=env,
    )


def build(command: str, destination: Path = GENERATED_DIR) -> None:
    reviewing = command in {"review", "release"}
    if reviewing:
        check()
    tools = doctor(simulation=reviewing)
    before = source_hashes()
    design = definition.load()
    with staged_output(destination) as out:
        generate(design, out)
        checks = ["generation"]
        if reviewing:
            native_checks(out)
            tests(out)
            if command == "release":
                physical_evidence()
            checks += [
                "ERC",
                "DRC and schematic parity",
                "unit and SPICE tests",
            ]
            previews(out)
            checks.append("previews")
        if command == "release":
            fabrication(out)
            checks += ["physical evidence", "manufacturing exports"]
        if source_hashes() != before:
            raise RuntimeError(
                "source changed during build; refusing to publish mixed-version artifacts"
            )
        for transient in out.glob("*.kicad_prl"):
            transient.unlink()
        write_report(out, destination, design, tools, before, checks)
    print(f"{command}: published {destination}")


def write_report(
    out: Path,
    previous: Path,
    design: pcbnew.BOARD,
    tools: dict[str, str],
    sources: dict[str, str],
    checks: list[str],
) -> None:
    projection = definition.netlist(design)
    old_path = previous / "netlist.json"
    old: dict[str, object] = (
        json.loads(old_path.read_text())["projects"]["board"]
        if old_path.exists()
        else {}
    )
    changes: list[str] = []
    for key in ("components", "nets"):
        current = object_fields(projection[key])
        prior = object_fields(old.get(key, {}))
        changed = sorted(
            k for k in set(current) | set(prior) if current.get(k) != prior.get(k)
        )
        changes.append(f"- {key}: {', '.join(changed) if changed else 'unchanged'}")
    placements = {
        c.GetReference(): [
            pcbnew.ToMM(c.GetPosition().x) - ORIGIN_X_MM,
            ORIGIN_Y_MM - pcbnew.ToMM(c.GetPosition().y),
            c.GetOrientationDegrees(),
        ]
        for c in parts(design)
    }
    snapshot = {
        "placements": placements,
        "rules": json.loads((out / PROJECT.name).read_text())["board"][
            "design_settings"
        ],
    }
    old_snapshot_path = previous / "layout.json"
    old_snapshot: dict[str, object] = (
        json.loads(old_snapshot_path.read_text()) if old_snapshot_path.exists() else {}
    )
    for key, value in snapshot.items():
        changes.append(
            f"- {key}: {'unchanged' if value == old_snapshot.get(key) else 'changed; see layout.json'}"
        )
    (out / "layout.json").write_text(
        json.dumps(snapshot, indent=2, sort_keys=True) + "\n"
    )
    evidence = [
        name
        for name in ("hall-magnet.json",)
        if not (PCB_ROOT / "definition/evidence" / name).is_file()
    ]
    report = [
        "# PCB review",
        "",
        f"{design.GetTitleBlock().GetRevision()}: {len(parts(design))} components, {len(connections(design))} connections.",
        "",
        *changes,
        "",
        "## Checks",
        *[f"- Passed: {c}" for c in checks],
        "",
        f"Physical evidence missing: {', '.join(evidence) or 'none (release validates measurements)'}.",
        "",
        "Generation alone is not release approval.",
        "",
    ]
    (out / "review.md").write_text("\n".join(report))
    manifest = {
        "schema": 1,
        "revision": design.GetTitleBlock().GetRevision(),
        "sources": sources,
        "toolchain": tools,
        "checks": checks,
        "design_sha256": hashlib.sha256(
            json.dumps(projection, sort_keys=True).encode()
        ).hexdigest(),
        "artifacts": {
            str(p.relative_to(out)): digest(p)
            for p in sorted(out.rglob("*"))
            if p.is_file()
        },
    }
    (out / "manifest.json").write_text(
        json.dumps(manifest, indent=2, sort_keys=True) + "\n"
    )


def string_mapping(value: object) -> TypeGuard[Mapping[str, object]]:
    return isinstance(value, dict) and all(
        isinstance(key, str) for key in cast(Mapping[object, object], value)
    )


def object_fields(value: object) -> Mapping[str, object]:
    if not string_mapping(value):
        raise ValueError("expected JSON object with string keys")
    return value
