"""Portable GLB structure checks and fingerprints for PCB/CAD synchronization."""

import hashlib
import json
import re
import shutil
import struct
import subprocess
from functools import lru_cache
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import cast

HARDWARE = Path(__file__).resolve().parents[4]

_JSON_CHUNK = 0x4E4F534A
_BIN_CHUNK = 0x004E4942
_COMPONENT_BYTES = {5120: 1, 5121: 1, 5122: 2, 5123: 2, 5125: 4, 5126: 4}
_TYPE_COMPONENTS = {
    "SCALAR": 1,
    "VEC2": 2,
    "VEC3": 3,
    "VEC4": 4,
    "MAT2": 4,
    "MAT3": 9,
    "MAT4": 16,
}


def source_digest() -> str:
    digest = hashlib.sha256(json.dumps(toolchain_versions(), sort_keys=True).encode())
    for root in (HARDWARE / "pcb", HARDWARE / "shared"):
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
    # Declared exporter dependencies are part of the geometry contract.
    for path in (
        HARDWARE / "build_support.py",
        HARDWARE.parent / ".devcontainer/Dockerfile",
        HARDWARE.parent / "pyproject.toml",
    ):
        if path.is_file():
            digest.update(str(path.relative_to(HARDWARE.parent)).encode())
            digest.update(path.read_bytes())
    return digest.hexdigest()


def file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def glb_document(path: Path) -> dict[str, object]:
    data = path.read_bytes()
    if len(data) < 12:
        raise ValueError("GLB export is truncated")
    magic, version, length = struct.unpack_from("<3I", data)
    if magic != 0x46546C67 or version != 2 or length != len(data):
        raise ValueError("Invalid GLB 2.0 export")
    chunks: list[tuple[int, bytes]] = []
    offset = 12
    while offset < length:
        if offset + 8 > length:
            raise ValueError("GLB chunk bounds are invalid")
        chunk_length, chunk_type = struct.unpack_from("<2I", data, offset)
        offset += 8
        end = offset + chunk_length
        if chunk_length % 4 or end > length:
            raise ValueError("GLB chunk bounds are invalid")
        chunks.append((chunk_type, data[offset:end]))
        offset = end
    if not chunks or chunks[0][0] != _JSON_CHUNK:
        raise ValueError("GLB JSON chunk must be first")
    if sum(chunk_type == _JSON_CHUNK for chunk_type, _ in chunks) != 1:
        raise ValueError("GLB must contain exactly one JSON chunk")
    binaries = [chunk for chunk_type, chunk in chunks if chunk_type == _BIN_CHUNK]
    if len(binaries) > 1:
        raise ValueError("GLB must contain at most one BIN chunk")
    document = cast(object, json.loads(chunks[0][1]))
    if not isinstance(document, dict):
        raise ValueError("GLB JSON must be an object")
    typed_document = cast(dict[str, object], document)
    _validate_geometry(typed_document, binaries[0] if binaries else None)
    return typed_document


def _array(document: dict[str, object], key: str) -> list[object]:
    value = document.get(key)
    if not isinstance(value, list):
        raise ValueError(f"GLB {key} must be an array")
    return cast(list[object], value)


def _index(value: object, count: int, description: str) -> int:
    if type(value) is not int or not 0 <= value < count:
        raise ValueError(f"GLB {description} index is invalid")
    return value


def _nonnegative_integer(value: object, description: str) -> int:
    if type(value) is not int or value < 0:
        raise ValueError(f"GLB {description} must be a nonnegative integer")
    return value


def _validate_geometry(document: dict[str, object], binary: bytes | None) -> None:
    asset = document.get("asset")
    if (
        not isinstance(asset, dict)
        or cast(dict[str, object], asset).get("version") != "2.0"
    ):
        raise ValueError("GLB asset must declare version 2.0")

    meshes = _array(document, "meshes")
    accessors = _array(document, "accessors")
    views = _array(document, "bufferViews")
    buffers = _array(document, "buffers")
    used_accessors: set[int] = set()
    position_accessors: set[int] = set()
    for raw_mesh in meshes:
        if not isinstance(raw_mesh, dict):
            raise ValueError("GLB mesh must be an object")
        mesh = cast(dict[str, object], raw_mesh)
        primitives = mesh.get("primitives")
        if not isinstance(primitives, list) or not primitives:
            raise ValueError("GLB mesh primitives must be a nonempty array")
        for raw_primitive in cast(list[object], primitives):
            if not isinstance(raw_primitive, dict):
                raise ValueError("GLB primitive must be an object")
            primitive = cast(dict[str, object], raw_primitive)
            attributes = primitive.get("attributes")
            if not isinstance(attributes, dict) or not attributes:
                raise ValueError("GLB primitive attributes must be a nonempty object")
            typed_attributes = cast(dict[str, object], attributes)
            position_accessors.add(
                _index(
                    typed_attributes.get("POSITION"),
                    len(accessors),
                    "POSITION accessor",
                )
            )
            for accessor in typed_attributes.values():
                used_accessors.add(
                    _index(accessor, len(accessors), "primitive accessor")
                )
            if "indices" in primitive:
                used_accessors.add(
                    _index(primitive["indices"], len(accessors), "primitive accessor")
                )
            targets = primitive.get("targets", [])
            if not isinstance(targets, list):
                raise ValueError("GLB primitive targets are invalid")
            for raw_target in cast(list[object], targets):
                if not isinstance(raw_target, dict):
                    raise ValueError("GLB primitive targets are invalid")
                target = cast(dict[str, object], raw_target)
                for accessor in target.values():
                    used_accessors.add(
                        _index(accessor, len(accessors), "primitive accessor")
                    )

    used_views: dict[int, list[tuple[int, int, int]]] = {}
    for accessor_index in used_accessors:
        raw_accessor = accessors[accessor_index]
        if not isinstance(raw_accessor, dict):
            raise ValueError("GLB accessor must be an object")
        accessor = cast(dict[str, object], raw_accessor)
        view_index = _index(
            accessor.get("bufferView"), len(views), "accessor bufferView"
        )
        component_type = accessor.get("componentType")
        accessor_type = accessor.get("type")
        if accessor_index in position_accessors and (
            component_type != 5126 or accessor_type != "VEC3"
        ):
            raise ValueError("GLB POSITION accessor must use float VEC3 values")
        if (
            component_type not in _COMPONENT_BYTES
            or accessor_type not in _TYPE_COMPONENTS
        ):
            raise ValueError("GLB accessor format is invalid")
        count = _nonnegative_integer(accessor.get("count"), "accessor count")
        if count == 0:
            raise ValueError("GLB accessor count must be positive")
        byte_offset = _nonnegative_integer(
            accessor.get("byteOffset", 0), "accessor byteOffset"
        )
        element_bytes = (
            _COMPONENT_BYTES[cast(int, component_type)]
            * _TYPE_COMPONENTS[cast(str, accessor_type)]
        )
        used_views.setdefault(view_index, []).append(
            (byte_offset, element_bytes, count)
        )

    used_buffers: set[int] = set()
    for view_index, spans in used_views.items():
        raw_view = views[view_index]
        if not isinstance(raw_view, dict):
            raise ValueError("GLB bufferView must be an object")
        view = cast(dict[str, object], raw_view)
        buffer_index = _index(view.get("buffer"), len(buffers), "bufferView buffer")
        used_buffers.add(buffer_index)
        view_offset = _nonnegative_integer(
            view.get("byteOffset", 0), "bufferView byteOffset"
        )
        view_length = _nonnegative_integer(
            view.get("byteLength"), "bufferView byteLength"
        )
        stride = view.get("byteStride")
        for accessor_offset, element_length, count in spans:
            stride_value = element_length
            if stride is not None:
                stride_value = _nonnegative_integer(stride, "bufferView byteStride")
                if stride_value < element_length:
                    raise ValueError("GLB accessor bounds exceed its bufferView")
            required = accessor_offset + stride_value * (count - 1) + element_length
            if required > view_length:
                raise ValueError("GLB accessor bounds exceed its bufferView")
        raw_buffer = buffers[buffer_index]
        if not isinstance(raw_buffer, dict):
            raise ValueError("GLB buffer must be an object")
        buffer = cast(dict[str, object], raw_buffer)
        buffer_length = _nonnegative_integer(
            buffer.get("byteLength"), "buffer byteLength"
        )
        if view_offset + view_length > buffer_length:
            raise ValueError("GLB bufferView bounds exceed its buffer")

    for buffer_index in used_buffers:
        raw_buffer = cast(dict[str, object], buffers[buffer_index])
        if buffer_index != 0 or "uri" in raw_buffer:
            raise ValueError("GLB primitive buffer must use the embedded BIN chunk")
        if binary is None:
            raise ValueError("GLB primitive buffer is missing its BIN chunk")
        buffer_length = cast(int, raw_buffer["byteLength"])
        if buffer_length > len(binary) or len(binary) - buffer_length > 3:
            raise ValueError("GLB BIN chunk bounds do not match its buffer")


def check_component_coverage(path: Path, references: set[str]) -> None:
    document = glb_document(path)
    raw_nodes = document.get("nodes")
    meshes = document.get("meshes")
    if not isinstance(raw_nodes, list) or not isinstance(meshes, list):
        raise ValueError("GLB needs node and mesh arrays")
    node_count, mesh_count = (
        len(cast(list[object], raw_nodes)),
        len(cast(list[object], meshes)),
    )
    nodes: list[dict[str, object]] = []
    for raw in cast(list[object], raw_nodes):
        if not isinstance(raw, dict):
            raise ValueError("GLB node must be an object")
        node = cast(dict[str, object], raw)
        children = node.get("children", [])
        if not isinstance(children, list) or any(
            type(child) is not int or not 0 <= child < node_count
            for child in cast(list[object], children)
        ):
            raise ValueError("GLB child indices are invalid")
        if "mesh" in node and (
            type(node["mesh"]) is not int or not 0 <= node["mesh"] < mesh_count
        ):
            raise ValueError("GLB mesh index is invalid")
        name = node.get("name", "")
        if not isinstance(name, str):
            raise ValueError("GLB node name must be text")
        # KiCad names package roots by reference and artwork by OCC labels.
        if (
            name not in references
            and (children or re.fullmatch(r"[A-Z]+[0-9]+", name))
            and name
        ):
            raise ValueError(f"Unexpected GLB component: {name}")
        nodes.append(node)
    parents: set[int] = set()
    for node in nodes:
        for child in cast(list[int], node.get("children", [])):
            if child in parents:
                raise ValueError("GLB node has multiple parents")
            parents.add(child)
    # Validate the complete graph, including disconnected/unexpected nodes.
    active: set[int] = set()
    done: set[int] = set()

    def visit(index: int) -> None:
        if index in active:
            raise ValueError("GLB node graph contains a cycle")
        if index in done:
            return
        active.add(index)
        for child in cast(list[int], nodes[index].get("children", [])):
            visit(child)
        active.remove(index)
        done.add(index)

    try:
        for index in range(len(nodes)):
            visit(index)
    except RecursionError as error:
        raise ValueError("GLB hierarchy is too deep") from error
    owned_nodes: set[int] = set()
    for reference in references:
        matches = [node for node in nodes if node.get("name") == reference]
        if len(matches) != 1:
            raise ValueError(f"{reference}: missing or duplicate GLB component")
        pending = [matches[0]]
        has_mesh = False
        while pending:
            current = pending.pop()
            owned_nodes.add(id(current))
            has_mesh |= "mesh" in current
            pending.extend(
                nodes[index] for index in cast(list[int], current.get("children", []))
            )
        if not has_mesh:
            raise ValueError(f"{reference}: GLB component has no mesh")
    for node in nodes:
        # KiCad's board/artwork nodes use OpenCascade assembly labels.
        if (
            "mesh" in node
            and id(node) not in owned_nodes
            and not str(node.get("name", "")).startswith("=>[")
        ):
            raise ValueError(
                "GLB contains geometry outside the declared components or KiCad artwork"
            )


@lru_cache(maxsize=1)
def toolchain_versions() -> dict[str, str]:
    """Actual exporter versions supplement the declared devcontainer pins."""
    versions: dict[str, str] = {}
    for package in ("cadquery", "cadquery-ocp"):
        try:
            versions[package] = version(package)
        except PackageNotFoundError:
            versions[package] = "unavailable"
    command = shutil.which("kicad-cli")
    versions["kicad"] = (
        subprocess.run(
            (command, "version"), check=True, capture_output=True, text=True, timeout=10
        ).stdout.strip()
        if command
        else "unavailable"
    )
    return versions
