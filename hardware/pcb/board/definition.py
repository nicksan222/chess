"""Compose this chess board's reviewed definitions from reusable models."""

from __future__ import annotations

from collections.abc import Mapping

from board import hall_banks, placement
from components.catalog import for_netlist_entry
from domain import connectivity, sources
from domain.design import BoardDesign, ComponentInstance, ComponentSpec
from domain.envelope import BoardEnvelope


def envelope() -> BoardEnvelope:
    """The physical chess-board envelope from shared mechanical definitions."""
    dimensions = sources.dimensions()
    width, height, _thickness = dimensions.PCB_SIZE_MM
    return BoardEnvelope(width, height, dimensions.PLAYING_SPAN_MM / 2.0)


def load() -> BoardDesign:
    """Load and validate the checked-in chess-board contract."""
    return from_contract(sources.netlist())


def from_contract(contract: Mapping[str, object]) -> BoardDesign:
    """Compose a typed graph from authoritative ``connections``.

    The serialized ``nets`` field is a compatibility projection, checked against
    named connections by the contract tests rather than consumed here.
    """
    raw_components = contract.get("components")
    raw_connections = contract.get("connections")
    if not isinstance(raw_components, Mapping):
        raise ValueError("board components must be a mapping")
    if not isinstance(raw_connections, list):
        raise ValueError("board connections must be a list")

    specs = {
        reference: ComponentSpec.from_contract(reference, entry)
        for reference, entry in raw_components.items()
        if isinstance(reference, str) and isinstance(entry, Mapping)
    }
    if len(specs) != len(raw_components):
        raise ValueError("component references and entries have invalid types")
    models = {
        reference: for_netlist_entry(reference, raw_components[reference])
        for reference in specs
    }
    placed = tuple(placement.build(contract))
    by_reference = {item.reference: item for item in placed}
    if set(by_reference) != set(specs):
        raise ValueError("placements do not exactly cover board components")

    graph = connectivity.ConnectionGraph.from_contract(
        raw_connections,
        placed,
        models,
    )
    instances = {
        reference: ComponentInstance(spec, models[reference], by_reference[reference])
        for reference, spec in specs.items()
    }
    title = contract.get("title")
    revision = contract.get("revision")
    if not isinstance(title, str) or not isinstance(revision, str):
        raise ValueError("board title and revision must be strings")
    design = BoardDesign.create(
        title=title,
        revision=revision,
        components=instances,
        connections=graph,
        placements=placed,
    )
    hall_banks.validate(design)
    return design
