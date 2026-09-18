"""Build a reviewer-focused pull-request report from generated PCB artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, cast

GENERATED = Path("hardware/pcb/generated")
MARKER = "<!-- pcb-review-report -->"
CHANGE_MARKER = "<!-- pcb-design-changed: {changed} -->"
MAX_DETAILS = 24


@dataclass(frozen=True)
class BoardSnapshot:
    """Stable copper facts extracted from a native KiCad board."""

    tracks: frozenset[tuple[str, str, tuple[float, float], tuple[float, float], float]]
    vias: frozenset[tuple[str, tuple[float, float], float, float, tuple[str, ...]]]
    zones: frozenset[tuple[str, tuple[str, ...], tuple[float, float, float, float]]]
    board_sha256: str


def _json_object(value: object, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ValueError(f"{label} must be a JSON object")
    mapping = cast(dict[object, object], value)
    if not all(isinstance(key, str) for key in mapping):
        raise ValueError(f"{label} must be a JSON object")
    return cast(dict[str, Any], mapping)


def _load_json(path: Path) -> dict[str, Any]:
    return _json_object(json.loads(path.read_text()), str(path))


def _git_file(ref: str, path: Path) -> bytes | None:
    result = subprocess.run(
        ["git", "show", f"{ref}:{path.as_posix()}"],
        check=False,
        capture_output=True,
    )
    return result.stdout if result.returncode == 0 else None


def _base_json(ref: str, name: str) -> dict[str, Any] | None:
    contents = _git_file(ref, GENERATED / name)
    if contents is None:
        return None
    return _json_object(json.loads(contents), f"{ref}:{name}")


def _project(netlist: dict[str, Any]) -> dict[str, Any]:
    projects = _json_object(netlist.get("projects"), "netlist projects")
    return _json_object(projects.get("board"), "netlist board")


def _mapping(value: object, label: str) -> dict[str, Any]:
    return _json_object(value, label)


def _endpoint(value: object) -> str:
    if not isinstance(value, list):
        raise ValueError("net endpoint must be a two-item list")
    parts = cast(list[object], value)
    if len(parts) != 2:
        raise ValueError("net endpoint must be a two-item list")
    return f"{parts[0]}.{parts[1]}"


def _millimetres(pcbnew: Any, value: int) -> float:
    return round(float(pcbnew.ToMM(value)), 3)


def _point(pcbnew: Any, value: Any) -> tuple[float, float]:
    return (_millimetres(pcbnew, value.x), _millimetres(pcbnew, value.y))


def board_snapshot(path: Path) -> BoardSnapshot:
    """Load track, via, and zone geometry using KiCad's native Python API."""
    try:
        import pcbnew
    except ImportError as error:
        raise RuntimeError(
            "KiCad pcbnew is required to generate the PR report"
        ) from error

    board = pcbnew.LoadBoard(str(path))
    tracks: set[tuple[str, str, tuple[float, float], tuple[float, float], float]] = (
        set()
    )
    vias: set[tuple[str, tuple[float, float], float, float, tuple[str, ...]]] = set()
    for item in board.GetTracks():
        if isinstance(item, pcbnew.PCB_VIA):
            layers = tuple(
                board.GetLayerName(layer) for layer in item.GetLayerSet().CuStack()
            )
            vias.add(
                (
                    item.GetNetname(),
                    _point(pcbnew, item.GetPosition()),
                    _millimetres(pcbnew, item.GetWidth(pcbnew.F_Cu)),
                    _millimetres(pcbnew, item.GetDrillValue()),
                    layers,
                )
            )
            continue
        endpoints = sorted(
            (_point(pcbnew, item.GetStart()), _point(pcbnew, item.GetEnd()))
        )
        tracks.add(
            (
                item.GetNetname(),
                board.GetLayerName(item.GetLayer()),
                endpoints[0],
                endpoints[1],
                _millimetres(pcbnew, item.GetWidth()),
            )
        )

    zones: set[tuple[str, tuple[str, ...], tuple[float, float, float, float]]] = set()
    for zone in board.Zones():
        bounds = zone.GetBoundingBox()
        layers = tuple(
            board.GetLayerName(layer) for layer in zone.GetLayerSet().CuStack()
        )
        zones.add(
            (
                zone.GetNetname(),
                layers,
                (
                    _millimetres(pcbnew, bounds.GetLeft()),
                    _millimetres(pcbnew, bounds.GetTop()),
                    _millimetres(pcbnew, bounds.GetRight()),
                    _millimetres(pcbnew, bounds.GetBottom()),
                ),
            )
        )

    return BoardSnapshot(
        tracks=frozenset(tracks),
        vias=frozenset(vias),
        zones=frozenset(zones),
        board_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def _base_board(ref: str) -> BoardSnapshot | None:
    contents = _git_file(ref, GENERATED / "chess-board.kicad_pcb")
    if contents is None:
        return None
    with tempfile.TemporaryDirectory(prefix="pcb-pr-report-") as directory:
        path = Path(directory) / "base.kicad_pcb"
        path.write_bytes(contents)
        return board_snapshot(path)


def _git_text(*arguments: str) -> str:
    result = subprocess.run(
        ["git", *arguments],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def _repository_from_origin() -> str | None:
    remote = _git_text("remote", "get-url", "origin").removesuffix(".git")
    if "://" in remote:
        path = remote.split("://", maxsplit=1)[1].split("/", maxsplit=1)
        return path[1] if len(path) == 2 else None
    if ":" in remote:
        return remote.split(":", maxsplit=1)[1]
    return None


def _run_url(repository: str | None) -> str | None:
    server = os.environ.get("GITHUB_SERVER_URL", "https://github.com")
    run_id = os.environ.get("GITHUB_RUN_ID")
    if repository is None:
        return None
    suffix = f"/runs/{run_id}" if run_id else ""
    return f"{server}/{repository}/actions{suffix}"


def _signed(value: int) -> str:
    return f"{value:+d}" if value else "0"


def _limited(items: list[str]) -> list[str]:
    visible = items[:MAX_DETAILS]
    if len(items) > MAX_DETAILS:
        visible.append(f"…and {len(items) - MAX_DETAILS} more")
    return visible


def _details(summary: str, items: list[str]) -> list[str]:
    if not items:
        return []
    return [
        "<details>",
        f"<summary>{summary}</summary>",
        "",
        *[f"- {item}" for item in _limited(items)],
        "",
        "</details>",
        "",
    ]


def _component_label(reference: str, component: object) -> str:
    fields = _mapping(component, f"component {reference}")
    description = str(fields.get("description", "component"))
    value = str(fields.get("value", ""))
    package = str(fields.get("package", ""))
    specifics = ", ".join(item for item in (value, package) if item)
    return f"`{reference}` — {description}" + (f" ({specifics})" if specifics else "")


def _component_changes(
    base: dict[str, Any], current: dict[str, Any]
) -> tuple[str, list[str]]:
    before = _mapping(base.get("components", {}), "base components")
    after = _mapping(current.get("components", {}), "current components")
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    modified = sorted(
        key for key in set(before) & set(after) if before[key] != after[key]
    )
    details = [f"Added {_component_label(key, after[key])}" for key in added]
    details += [f"Removed {_component_label(key, before[key])}" for key in removed]
    for key in modified:
        old_fields = _mapping(before[key], f"base component {key}")
        new_fields = _mapping(after[key], f"current component {key}")
        fields = sorted(
            name
            for name in set(old_fields) | set(new_fields)
            if old_fields.get(name) != new_fields.get(name)
        )
        details.append(f"Changed `{key}`: {', '.join(fields)}")
    summary = (
        f"{len(after)} total ({_signed(len(added))} added, "
        f"{_signed(-len(removed))} removed, {len(modified)} modified)"
    )
    return summary, details


def _net_changes(
    base: dict[str, Any], current: dict[str, Any]
) -> tuple[str, list[str]]:
    before = _mapping(base.get("nets", {}), "base nets")
    after = _mapping(current.get("nets", {}), "current nets")
    added = sorted(set(after) - set(before))
    removed = sorted(set(before) - set(after))
    rewired = sorted(
        key for key in set(before) & set(after) if before[key] != after[key]
    )
    details: list[str] = []
    for name in added:
        pins = ", ".join(_endpoint(item) for item in after[name])
        details.append(f"Added net `{name}`: {pins}")
    for name in removed:
        pins = ", ".join(_endpoint(item) for item in before[name])
        details.append(f"Removed net `{name}`: {pins}")
    for name in rewired:
        old_pins = {_endpoint(item) for item in before[name]}
        new_pins = {_endpoint(item) for item in after[name]}
        additions = ", ".join(f"+{pin}" for pin in sorted(new_pins - old_pins))
        removals = ", ".join(f"−{pin}" for pin in sorted(old_pins - new_pins))
        changes = ", ".join(filter(None, (additions, removals)))
        details.append(f"Rewired `{name}`: {changes}")
    summary = (
        f"{len(after)} nets ({_signed(len(added))} added, "
        f"{_signed(-len(removed))} removed, {len(rewired)} rewired)"
    )
    return summary, details


def _placement_changes(
    base_layout: dict[str, Any], current_layout: dict[str, Any]
) -> tuple[str, list[str]]:
    before = _mapping(base_layout.get("placements", {}), "base placements")
    after = _mapping(current_layout.get("placements", {}), "current placements")
    changed = sorted(
        key for key in set(before) | set(after) if before.get(key) != after.get(key)
    )
    details: list[str] = []
    for reference in changed:
        if reference not in before:
            details.append(f"Placed `{reference}` at {after[reference]}")
        elif reference not in after:
            details.append(f"Removed placement for `{reference}`")
        else:
            details.append(
                f"Moved `{reference}`: {before[reference]} → {after[reference]}"
            )
    return f"{len(after)} footprints ({len(changed)} changed)", details


def _flatten(value: object, prefix: str = "") -> dict[str, object]:
    if not isinstance(value, dict):
        return {prefix: value}
    mapping = cast(dict[object, object], value)
    flattened: dict[str, object] = {}
    for key, child in mapping.items():
        name = f"{prefix}.{key}" if prefix else str(key)
        flattened.update(_flatten(child, name))
    return flattened


def _rule_changes(
    base_layout: dict[str, Any], current_layout: dict[str, Any]
) -> tuple[str, list[str]]:
    before = _flatten(base_layout.get("rules", {}))
    after = _flatten(current_layout.get("rules", {}))
    changed = sorted(
        key for key in set(before) | set(after) if before.get(key) != after.get(key)
    )
    details = [
        f"`{key}`: `{before.get(key, 'not set')}` → `{after.get(key, 'not set')}`"
        for key in changed
    ]
    return f"{len(changed)} settings changed", details


def _copper_changes(
    base: BoardSnapshot | None, current: BoardSnapshot
) -> tuple[str, list[str]]:
    if base is None:
        return (
            (
                f"{len(current.tracks)} segments, {len(current.vias)} vias, "
                f"{len(current.zones)} zones (no base board)"
            ),
            [],
        )
    added_tracks = current.tracks - base.tracks
    removed_tracks = base.tracks - current.tracks
    added_vias = current.vias - base.vias
    removed_vias = base.vias - current.vias
    added_zones = current.zones - base.zones
    removed_zones = base.zones - current.zones
    details: list[str] = []
    track_groups = Counter((track[0], track[1]) for track in added_tracks)
    removed_groups = Counter((track[0], track[1]) for track in removed_tracks)
    for net, layer in sorted(set(track_groups) | set(removed_groups)):
        details.append(
            f"`{net}` on {layer}: +{track_groups[net, layer]} / "
            f"−{removed_groups[net, layer]} track segments"
        )
    via_groups = Counter(via[0] for via in added_vias)
    removed_via_groups = Counter(via[0] for via in removed_vias)
    for net in sorted(set(via_groups) | set(removed_via_groups)):
        details.append(f"`{net}`: +{via_groups[net]} / −{removed_via_groups[net]} vias")
    for net, layers, _bounds in sorted(added_zones):
        details.append(f"Added `{net}` copper zone on {', '.join(layers)}")
    for net, layers, _bounds in sorted(removed_zones):
        details.append(f"Removed `{net}` copper zone on {', '.join(layers)}")
    changed = sum(
        len(items)
        for items in (
            added_tracks,
            removed_tracks,
            added_vias,
            removed_vias,
            added_zones,
            removed_zones,
        )
    )
    summary = (
        f"{len(current.tracks)} segments "
        f"({_signed(len(added_tracks) - len(removed_tracks))}), "
        f"{len(current.vias)} vias ({_signed(len(added_vias) - len(removed_vias))}), "
        f"{len(current.zones)} zones "
        f"({_signed(len(added_zones) - len(removed_zones))}); "
        f"{changed} geometry changes"
    )
    if current.board_sha256 != base.board_sha256 and not details:
        details.append("Native board file changed outside tracked copper geometry")
    return summary, details


def _violations(current: Path) -> str:
    erc = _load_json(current / "erc.json")
    sheets = erc.get("sheets", [])
    erc_count = sum(len(sheet.get("violations", [])) for sheet in sheets)
    drc = _load_json(current / "drc.json")
    drc_count = len(drc.get("violations", []))
    unconnected = len(drc.get("unconnected_items", []))
    parity = len(drc.get("schematic_parity", []))
    return (
        f"ERC {erc_count}, DRC {drc_count}, unconnected {unconnected}, "
        f"schematic parity {parity}"
    )


def build_report(
    *,
    base_ref: str,
    head_ref: str,
    current: Path,
    repository: str | None,
    run_url: str | None,
) -> str:
    current_netlist = _project(_load_json(current / "netlist.json"))
    base_netlist_document = _base_json(base_ref, "netlist.json")
    base_netlist = _project(base_netlist_document) if base_netlist_document else {}
    current_layout = _load_json(current / "layout.json")
    base_layout = _base_json(base_ref, "layout.json") or {}
    current_board = board_snapshot(current / "chess-board.kicad_pcb")
    base_board = _base_board(base_ref)

    component_summary, component_details = _component_changes(
        base_netlist, current_netlist
    )
    net_summary, net_details = _net_changes(base_netlist, current_netlist)
    placement_summary, placement_details = _placement_changes(
        base_layout, current_layout
    )
    rule_summary, rule_details = _rule_changes(base_layout, current_layout)
    copper_summary, copper_details = _copper_changes(base_board, current_board)

    manifest = _load_json(current / "manifest.json")
    checks = manifest.get("checks", [])
    revision = current_netlist.get("revision", "unknown revision")
    semantic_changes = any(
        (
            component_details,
            net_details,
            placement_details,
            rule_details,
            copper_details,
        )
    )
    status = (
        "PCB design changes detected; review the sections below."
        if semantic_changes
        else "No electrical, placement, rule, or copper changes detected."
    )
    board_link = None
    if repository:
        board_link = (
            f"https://github.com/{repository}/blob/{head_ref}/"
            "hardware/pcb/generated/chess-board.kicad_pcb"
        )

    lines = [
        MARKER,
        CHANGE_MARKER.format(changed=str(semantic_changes).lower()),
        "## PCB change report",
        "",
        f"**{revision}: {status}**",
        "",
        f"Compared `{base_ref[:12]}` to `{head_ref[:12]}`.",
        "",
        "| Review surface | Result |",
        "| --- | --- |",
        f"| Components | {component_summary} |",
        f"| Wiring / nets | {net_summary} |",
        f"| Placement | {placement_summary} |",
        f"| Design rules | {rule_summary} |",
        f"| Copper | {copper_summary} |",
        f"| Native checks | {_violations(current)} |",
        "",
        *_details("Component changes", component_details),
        *_details("Wiring changes", net_details),
        *_details("Placement changes", placement_details),
        *_details("Design-rule changes", rule_details),
        *_details("Copper changes", copper_details),
        "### Evidence",
        "",
        f"- Passed: {', '.join(str(check) for check in checks)}",
        *([f"- [Open the generated board]({board_link})"] if board_link else []),
        *(
            [
                f"- [Open board renders, schematics, BOMs, and reports]({run_url}#artifacts)"
            ]
            if run_url
            else []
        ),
        "- Physical Hall/magnet evidence remains a separate release gate.",
        "",
        "_This comment is updated automatically after each CI run._",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-ref", default="main")
    parser.add_argument("--head-ref", default=None)
    parser.add_argument("--current", type=Path, default=GENERATED)
    parser.add_argument("--repository", default=None)
    parser.add_argument("--run-url", default=None)
    parser.add_argument("--output", type=Path, default=Path("pcb-pr-report.md"))
    args = parser.parse_args()
    repository = args.repository or _repository_from_origin()
    report = build_report(
        base_ref=args.base_ref,
        head_ref=args.head_ref or _git_text("rev-parse", "HEAD"),
        current=args.current,
        repository=repository,
        run_url=args.run_url or _run_url(repository),
    )
    args.output.write_text(report)


if __name__ == "__main__":
    main()
