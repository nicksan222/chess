"""Missing component meshes must fail export rather than disappear from CAD."""

import json
import struct
import tempfile
import unittest
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast
from unittest.mock import patch

from .model_export import check_component_coverage, glb_document, source_digest

TRIANGLE = struct.pack(
    "<9f3H",
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0.0,
    0.0,
    1.0,
    0.0,
    0,
    1,
    2,
)


def write_glb(
    path: Path, document: Mapping[str, object], binary: bytes | None = TRIANGLE
) -> None:
    chunk = json.dumps(document).encode()
    chunk += b" " * (-len(chunk) % 4)
    chunks = struct.pack("<2I", len(chunk), 0x4E4F534A) + chunk
    if binary is not None:
        binary += b"\0" * (-len(binary) % 4)
        chunks += struct.pack("<2I", len(binary), 0x004E4942) + binary
    path.write_bytes(struct.pack("<3I", 0x46546C67, 2, 12 + len(chunks)) + chunks)


def glb(path: Path, nodes: Sequence[Mapping[str, object]]) -> None:
    count = (
        max(
            (cast(int, n["mesh"]) for n in nodes if isinstance(n.get("mesh"), int)),
            default=-1,
        )
        + 1
    )
    write_glb(
        path,
        {
            "asset": {"version": "2.0"},
            "nodes": nodes,
            "meshes": [
                {
                    "primitives": [
                        {"attributes": {"POSITION": 0}, "indices": 1, "mode": 4}
                    ]
                }
                for _ in range(count)
            ],
            "accessors": [
                {
                    "bufferView": 0,
                    "componentType": 5126,
                    "count": 3,
                    "type": "VEC3",
                },
                {
                    "bufferView": 1,
                    "componentType": 5123,
                    "count": 3,
                    "type": "SCALAR",
                },
            ],
            "bufferViews": [
                {"buffer": 0, "byteOffset": 0, "byteLength": 36},
                {"buffer": 0, "byteOffset": 36, "byteLength": 6},
            ],
            "buffers": [{"byteLength": len(TRIANGLE)}],
        },
    )


class ModelExportTest(unittest.TestCase):
    def test_missing_empty_or_duplicate_components_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "board.glb"
            for nodes in (
                [],
                [{"name": "SW1"}],
                [{"name": "SW1", "mesh": 0}, {"name": "SW1", "mesh": 1}],
            ):
                with self.subTest(nodes=nodes):
                    glb(path, nodes)
                    with self.assertRaises(ValueError):
                        check_component_coverage(path, {"SW1"})

    def test_child_mesh_is_covered_and_truncated_glb_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "board.glb"
            glb(path, [{"name": "SW1", "children": [1]}, {"mesh": 0}])
            check_component_coverage(path, {"SW1"})
            path.write_bytes(path.read_bytes()[:-1])
            with self.assertRaises(ValueError):
                glb_document(path)

    def test_invalid_graphs_and_unexpected_packages_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "board.glb"
            for nodes in (
                [{"name": "SW1", "children": [99]}],
                [{"name": "SW1", "children": [0]}],
                [{"name": "SW1", "children": [-1]}],
                [{"name": "SW1", "children": ["x"]}],
                [{"name": "SW1", "children": None}],
                [{"name": "SW1", "mesh": "x"}],
                [{"name": "SW1", "mesh": 0}, {"name": "StrayBody", "mesh": 1}],
                [
                    {"name": "SW1", "mesh": 0},
                    {"name": "X1", "children": [2]},
                    {"mesh": 0},
                ],
            ):
                with self.subTest(nodes=nodes):
                    glb(path, nodes)
                    with self.assertRaises(ValueError):
                        check_component_coverage(path, {"SW1"})

    def test_missing_bin_and_invalid_used_geometry_references_fail(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "board.glb"
            glb(path, [{"name": "SW1", "mesh": 0}])
            valid = glb_document(path)
            malformed: list[tuple[str, dict[str, object], bytes | None]] = []

            missing_asset = dict(valid)
            missing_asset.pop("asset")
            malformed.append(("asset", missing_asset, TRIANGLE))

            no_primitives = dict(valid)
            no_primitives["meshes"] = [{}]
            malformed.append(("primitives", no_primitives, TRIANGLE))

            missing_position = dict(valid)
            missing_position["meshes"] = [
                {"primitives": [{"attributes": {"NORMAL": 0}}]}
            ]
            malformed.append(("POSITION", missing_position, TRIANGLE))

            wrong_position_format = dict(valid)
            accessors = cast(list[object], valid["accessors"])
            wrong_position_format["accessors"] = [
                {**cast(dict[str, object], accessors[0]), "type": "VEC2"},
                accessors[1],
            ]
            malformed.append(("POSITION", wrong_position_format, TRIANGLE))

            invalid_accessor = dict(valid)
            invalid_accessor["meshes"] = [
                {"primitives": [{"attributes": {"POSITION": 99}}]}
            ]
            malformed.append(("accessor", invalid_accessor, TRIANGLE))

            invalid_view = dict(valid)
            invalid_view["accessors"] = [
                {**cast(dict[str, object], accessors[0]), "bufferView": 99},
                accessors[1],
            ]
            malformed.append(("bufferView", invalid_view, TRIANGLE))

            invalid_buffer = dict(valid)
            views = cast(list[object], valid["bufferViews"])
            invalid_buffer["bufferViews"] = [
                {**cast(dict[str, object], views[0]), "buffer": 99},
                views[1],
            ]
            malformed.append(("buffer", invalid_buffer, TRIANGLE))

            oversized_view = dict(valid)
            oversized_view["bufferViews"] = [
                {**cast(dict[str, object], views[0]), "byteLength": 999},
                views[1],
            ]
            malformed.append(("bounds", oversized_view, TRIANGLE))

            malformed.append(("BIN", valid, None))

            for expected, document, binary in malformed:
                with self.subTest(expected=expected):
                    write_glb(path, document, binary)
                    with self.assertRaisesRegex(ValueError, expected):
                        glb_document(path)

    def test_glb_chunk_bounds_are_checked_before_json_is_read(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "board.glb"
            glb(path, [{"name": "SW1", "mesh": 0}])
            damaged = bytearray(path.read_bytes())
            struct.pack_into("<I", damaged, 12, len(damaged))
            path.write_bytes(damaged)
            with self.assertRaisesRegex(ValueError, "chunk bounds"):
                glb_document(path)

    def test_exporter_configuration_invalidates_source_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            hardware = root / "hardware"
            hardware.mkdir()
            (root / ".devcontainer").mkdir()
            config = root / ".devcontainer/Dockerfile"
            config.write_text("cadquery==2.6.1")
            build_support = hardware / "build_support.py"
            build_support.write_text("VERSION = 1")
            with patch("pcb.harness.base.pcbnew.model_export.HARDWARE", hardware):
                before = source_digest()
                config.write_text("cadquery==2.6.2")
                self.assertNotEqual(before, source_digest())
                after_config = source_digest()
                build_support.write_text("VERSION = 2")
                self.assertNotEqual(after_config, source_digest())

    def test_installed_toolchain_version_changes_invalidate_export(self) -> None:
        with patch(
            "pcb.harness.base.pcbnew.model_export.toolchain_versions",
            return_value={"kicad": "9.0.8"},
        ):
            before = source_digest()
        with patch(
            "pcb.harness.base.pcbnew.model_export.toolchain_versions",
            return_value={"kicad": "9.0.9"},
        ):
            self.assertNotEqual(before, source_digest())
