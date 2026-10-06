"""One build pipeline; reviewed outputs are published only as complete sets.

Role: orchestrates everything that turns the Python board definition into reviewed
artifacts under `generated/`. Commands (see `build()`):

- `generate`: load the board, write schematic/BOM/netlist, route, write the
  native board and DSN.
- `review`: generate, then ERC, DRC with schematic parity, the unit/SPICE tests,
  and preview renders, after the source checks.
- `release`: review, plus the physical Hall/magnet evidence gate, then
  fabrication exports (Gerbers, drills).

Everything is built in a staging directory (`build_support.staged_output`) and
swapped into place only on success, so a failed run never leaves a mixed set. The
manifest records source and tool hashes so a reviewer can tie output to its inputs.
A passing run is evidence about the design files only, not about a physical board.
"""

from __future__ import annotations

import ast
import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import TypeGuard, cast

import pcbnew
from build_support import staged_output

from pcb.definition import board as definition
from pcb.definition.native import ORIGIN_X_MM, ORIGIN_Y_MM, connections, parts
from shared.json_values import parse_json

PCB_ROOT = Path(__file__).resolve().parent
REPOSITORY_ROOT = PCB_ROOT.parents[1]
# `PCB_OUTPUT` redirects all output (tests and the review step use it so they do
# not touch the checked-in `generated/` directory).
GENERATED_DIR = Path(os.environ.get("PCB_OUTPUT", PCB_ROOT / "generated"))
TESTS_CHECK = "unit and SPICE tests"
# Names of the published files inside GENERATED_DIR (or a staging copy of it).
BOARD = GENERATED_DIR / "chess-board.kicad_pcb"
DSN = GENERATED_DIR / "chess-board.dsn"
PROJECT = GENERATED_DIR / "chess-board.kicad_pro"
SCHEMATIC = GENERATED_DIR / "chess-board.kicad_sch"
SYMBOL_LIBRARY = GENERATED_DIR / "generated-symbols.kicad_sym"
SYMBOL_TABLE = GENERATED_DIR / "sym-lib-table"
BOM = GENERATED_DIR / "bom.md"
ASSEMBLY_BOM = GENERATED_DIR / "assembly-bom.csv"
HARNESS = GENERATED_DIR / "harness.md"
DESIGN_RULES = GENERATED_DIR / "chess-board.kicad_dru"
BOARD_TOP_SVG = GENERATED_DIR / "board-top.svg"
BOARD_BOTTOM_SVG = GENERATED_DIR / "board-bottom.svg"


def run(
    *args: str, output: Path | None = None, env: dict[str, str] | None = None
) -> str:
    """Run a tool from the repo root; return its output or raise RuntimeError.

    stdout and stderr are combined. If `output` is given the full text is saved
    there (e.g. a test log) even on failure; the error message keeps only the last
    12000 characters so a noisy failure stays readable.
    """
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
    """Check the toolchain and return its versions for the manifest.

    `kicad-cli` is always required; `ngspice` only when `simulation` is true
    (review/release run the SPICE scenarios). KiCad 9 is required because the
    file formats and `pcbnew` API this code writes are version specific.
    """
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
    """Hash every input that can change the output, keyed by repo-relative path.

    Covers the PCB and shared Python/JSON sources plus build config, but not
    `generated/` or caches. Taken before and after a build: if they differ, a
    source changed mid-build and publishing would mix versions (see `build()`).
    """
    roots = (PCB_ROOT, PCB_ROOT.parent / "shared")
    files = [
        p
        for root in roots
        for p in root.rglob("*")
        if p.is_file()
        and p.suffix in {".py", ".pyi", ".json"}
        and not {"generated", "__pycache__"}.intersection(p.parts)
    ]
    files.extend(
        (
            PCB_ROOT / "justfile",
            REPOSITORY_ROOT / "pyproject.toml",
            PCB_ROOT.parent / "build_support.py",
        )
    )
    return {str(p.relative_to(REPOSITORY_ROOT)): digest(p) for p in sorted(files)}


def generate(design: pcbnew.BOARD, out: Path) -> None:
    """Write all derived files and the routed native board into `out`.

    Order matters: project/BOM/netlist/schematic are taken from the *unrouted*
    board (connectivity does not depend on routing); then tracks and power planes
    are added, and the board is written, filled and exported to DSN.
    """
    # Deferred imports: only generation needs the output and routing modules.
    from pcb.definition import native
    from pcb.definition.output import exports, schematic
    from pcb.definition.routing import policies as routing
    from shared.electronics.harness import render_harness_table

    (out / PROJECT.name).write_text(exports.render_project())
    (out / DESIGN_RULES.name).write_text(exports.render_design_rules())
    (out / BOM.name).write_text(exports.render_bom(design))
    (out / ASSEMBLY_BOM.name).write_text(exports.render_assembly_csv(design))
    (out / HARNESS.name).write_text(render_harness_table())
    (out / "netlist.json").write_text(
        json.dumps(
            {"schema": 1, "projects": {"board": definition.netlist(design)}},
            indent=2,
            sort_keys=True,
        )
        + "\n"
    )
    schematic.write(design, out)
    # Mutates `design`: adds tracks, vias, then the three rail zones.
    routing.route(design)
    native.add_power_planes(design)
    native.write_board(design, out / BOARD.name, out / DSN.name)
    # pcbnew writes defaults beside the board while filling; reviewed settings win.
    (out / PROJECT.name).write_text(exports.render_project())


def native_checks(out: Path) -> None:
    """KiCad's own ERC and DRC (with schematic parity) must report nothing.

    Reports are saved in `out` (`erc.json`, `drc.json`, human-readable `drc.rpt`).
    The JSON reports are inspected rather than relying on exit status: any ERC
    violation, DRC violation, unconnected item, or schematic/PCB mismatch fails the
    build. Also exports `positions.csv` for assembly, in mm for both sides.
    """
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
    erc = object_fields(parse_json((out / "erc.json").read_text()))
    drc = object_fields(parse_json((out / "drc.json").read_text()))
    sheets = object_list(erc.get("sheets"))
    if any(object_fields(sheet).get("violations") for sheet in sheets) or any(
        drc.get(key) for key in ("violations", "unconnected_items", "schematic_parity")
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
    fill_position_packages(out / "positions.csv", out / BOARD.name)


def fill_position_packages(positions: Path, board_path: Path) -> None:
    """Write each part's approved package label into positions.csv (S4c).

    KiCad fills the Package column from the footprint library ID, which the
    generated footprints do not carry; the assembler needs the package.
    """
    design = pcbnew.LoadBoard(str(board_path))
    packages = {f.GetReference(): f.GetFieldText("Package") for f in parts(design)}
    rows = list(csv.reader(positions.read_text().splitlines()))
    header, body = rows[0], rows[1:]
    column = header.index("Package")
    for row in body:
        row[column] = packages[row[0]]
    # KiCad's own layout: bare header and numbers, quoted text columns.
    text = {header.index(name) for name in ("Ref", "Val", "Package", "Side")}
    lines = [",".join(header)]
    lines.extend(
        ",".join(f'"{v}"' if i in text else v for i, v in enumerate(row))
        for row in body
    )
    positions.write_text("\n".join(lines) + "\n")


def tests(out: Path) -> None:
    """Run the whole unit/SPICE suite against the freshly built output in `out`.

    Environment variables point the tests at the staging directory so they check
    the exact files about to be published. Log goes to `tests.log`.
    """
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
    """Export review images: schematic SVGs, top/bottom board SVGs, 3D renders.

    For human review only; no check consumes them. The bottom view is mirrored so
    text reads correctly as if the board were flipped over.
    """
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
    """True for a list whose every element is a finite positive number."""
    return isinstance(value, list) and all(
        _positive_number(v) for v in cast(list[object], value)
    )


def _positive_number(value: object) -> TypeGuard[int | float]:
    """Finite number > 0; rejects bool (a Python `int` subclass), NaN and inf."""
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value > 0
    )


def physical_evidence(path: Path | None = None) -> None:
    """Human Hall/magnet measurements are a production release gate, not a test skip.

    Validates the measurement record (default
    `definition/evidence/hall-magnet.json`) that a person produces on the real
    sensor and magnet. It must name the expected schema, board revision and sensor
    part, explicitly say `pass`, give the final assembled gap, and for each magnet
    pole list at least five positive operate and release distances (mm) plus notes.
    The smallest operate distance must be at least 0.5 mm more than the assembled gap, i.e. the
    sensor is measured to trigger with that much margin to spare. Only `release`
    calls it, before any fabrication file is written. A missing or failing record
    blocks fabrication on purpose; it cannot be replaced by software checks.
    """
    path = path or PCB_ROOT / "definition/evidence/hall-magnet.json"
    if not path.is_file():
        raise RuntimeError(f"missing physical evidence: {path}")
    record = object_fields(parse_json(path.read_text()))
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


def verification_gate() -> None:
    """Refuse release while a land is unverified or a design value is assumed."""
    from pcb.definition.verification import verification_blockers

    blockers = verification_blockers()
    if blockers:
        raise RuntimeError(
            "release blocked by open verification items:\n  " + "\n  ".join(blockers)
        )


def release_gates() -> None:
    """Run every release gate, then refuse once with all of their reasons."""
    failures: list[str] = []
    for gate in (physical_evidence, verification_gate):
        try:
            gate()
        except RuntimeError as error:
            failures.append(str(error))
    if failures:
        raise RuntimeError("release refused:\n" + "\n".join(failures))


def fabrication(out: Path) -> None:
    """Export Gerbers and Excellon drill files into `out/gerber`.

    All eight copper layers plus paste, silkscreen, mask and board outline. Drills
    are split plated/non-plated with slots as routed ovals, and a drill report is
    written. Runs only for `release`, after the physical evidence gate; producing
    these files does not mean they were sent to or accepted by a manufacturer.
    """
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
    """Non-publishing native-definition/dimensions checks; review also checks copper.

    Loads (and thereby validates) the board, runs Ruff lint and format checks, the
    strict type checker, and the dimensions unit tests. No generated files change.
    `BASEDPYRIGHT` can name another analyzer executable.
    """
    definition.load()
    run("ruff", "check", str(PCB_ROOT))
    run("ruff", "format", "--check", str(PCB_ROOT))
    analyzer = os.environ.get("BASEDPYRIGHT", "basedpyright")
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
    """Run `generate`, `review` or `release` and publish the result atomically.

    `destination` is replaced only if every step succeeds. Source hashes are taken
    before and after; a change in between aborts rather than publish artifacts built
    from two different versions of the source. Checks that actually ran are listed
    in the report, so it never claims more than was verified.
    """
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
                release_gates()
            checks += [
                "ERC",
                "DRC and schematic parity",
                TESTS_CHECK,
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
    old: Mapping[str, object] = (
        object_fields(
            object_fields(
                object_fields(parse_json(old_path.read_text())).get("projects")
            ).get("board")
        )
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
        "rules": object_fields(
            object_fields(parse_json((out / PROJECT.name).read_text())).get("board")
        ).get("design_settings"),
    }
    old_snapshot_path = previous / "layout.json"
    old_snapshot: Mapping[str, object] = (
        object_fields(parse_json(old_snapshot_path.read_text()))
        if old_snapshot_path.exists()
        else {}
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


def object_list(value: object) -> list[object]:
    if not isinstance(value, list):
        raise ValueError("expected JSON array")
    return cast(list[object], value)


def object_fields(value: object) -> Mapping[str, object]:
    if not string_mapping(value):
        raise ValueError("expected JSON object with string keys")
    return value
