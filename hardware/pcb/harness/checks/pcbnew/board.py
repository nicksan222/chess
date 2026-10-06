"""Automatic native checks for any rendered circuit registry.

These checks verify pad assignments and actual copper containment in closed
courtyards. Assigned nets are design intent; routed connectivity and copper
clearance still require the complete board's KiCad DRC gate.
"""

import math
from collections import Counter
from enum import StrEnum
from typing import cast

import pcbnew

from pcb.harness import BoardComponent, BoardRegistry
from pcb.harness.base.connections import NetConnection
from pcb.harness.base.geometry import Side


def validate_board(circuit: BoardRegistry, board: pcbnew.BOARD) -> None:
    """Reject omitted parts/pads, incorrect nets and broken native courtyards."""
    circuit.validate()
    footprints = list(board.GetFootprints())
    native = {footprint.GetReference(): footprint for footprint in footprints}
    declared = {component.reference for component in circuit.components()}
    if len(native) != len(footprints) or set(native) != declared:
        raise ValueError("native footprints must match the circuit registry exactly")
    for component in circuit.components():
        if not isinstance(component, BoardComponent):
            raise ValueError("native checks require BoardComponent instances")
        part = cast(BoardComponent[StrEnum], component)
        pattern = part.definition.land_pattern
        if pattern is None:
            raise ValueError(f"{part.reference}: missing land pattern")
        footprint = native[part.reference]
        pads = list(footprint.Pads())
        actual = {pad.GetNumber(): pad for pad in pads}
        if len(actual) != len(pads) or set(actual) != {
            pad.physical_number for pad in pattern.pads
        }:
            raise ValueError(f"{part.reference}: native pad coverage differs")
        for pad in pattern.pads:
            connection = part.pins[pad.pin]
            expected = (
                connection.net.label if isinstance(connection, NetConnection) else ""
            )
            if actual[pad.physical_number].GetNetname() != expected:
                raise ValueError(
                    f"{part.reference}/{pad.physical_number}: wrong or missing net"
                )

        layer = pcbnew.F_CrtYd if part.placement.side is Side.TOP else pcbnew.B_CrtYd
        edges = [
            item for item in footprint.GraphicalItems() if item.GetLayer() == layer
        ]
        if len(edges) != 4 or any(
            edge.GetShape() != pcbnew.SHAPE_T_SEGMENT for edge in edges
        ):
            raise ValueError(f"{part.reference}: courtyard needs four line segments")
        endpoints = Counter(
            (point.x, point.y)
            for edge in edges
            for point in (edge.GetStart(), edge.GetEnd())
        )
        if len(endpoints) != 4 or any(count != 2 for count in endpoints.values()):
            raise ValueError(f"{part.reference}: courtyard is not closed")
        centre_x = sum(point[0] for point in endpoints) / 4
        centre_y = sum(point[1] for point in endpoints) / 4
        corners = sorted(
            endpoints, key=lambda p: math.atan2(p[1] - centre_y, p[0] - centre_x)
        )
        expected_edges = {
            frozenset((start, end))
            for start, end in zip(corners, corners[1:] + corners[:1])
        }
        actual_edges = {
            frozenset(
                (
                    (edge.GetStart().x, edge.GetStart().y),
                    (edge.GetEnd().x, edge.GetEnd().y),
                )
            )
            for edge in edges
        }
        if actual_edges != expected_edges:
            raise ValueError(f"{part.reference}: courtyard is crossed or disconnected")
        courtyard = pcbnew.SHAPE_POLY_SET()
        courtyard.NewOutline()
        for x, y in corners:
            courtyard.Append(x, y)
        if courtyard.Area() <= 0:
            raise ValueError(f"{part.reference}: courtyard has no area")
        expected_area = (
            part.definition.courtyard.width_mm * part.definition.courtyard.height_mm
        )
        if not math.isclose(courtyard.Area() / 1e12, expected_area, abs_tol=0.00001):
            raise ValueError(
                f"{part.reference}: native courtyard differs from declaration"
            )
        copper_layer = pcbnew.F_Cu if part.placement.side is Side.TOP else pcbnew.B_Cu
        for pad in pads:
            copper = pcbnew.SHAPE_POLY_SET()
            pad.TransformShapeToPolygon(
                copper, copper_layer, 0, 1000, pcbnew.ERROR_INSIDE
            )
            if copper.Area() <= 0:
                raise ValueError(
                    f"{part.reference}/{pad.GetNumber()}: pad has no copper"
                )
            copper.BooleanSubtract(courtyard)
            if copper.Area() > 1:
                raise ValueError(
                    f"{part.reference}/{pad.GetNumber()}: copper exceeds courtyard"
                )
