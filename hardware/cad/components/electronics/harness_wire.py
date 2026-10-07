"""One named conductor swept along an explicit proposed assembly route."""

from __future__ import annotations

import math
from itertools import pairwise
from typing import TYPE_CHECKING

from cad.harness.base.component import Component
from shared.electronics.harness import HarnessWire as WireDefinition

if TYPE_CHECKING:
    import bpy

Point3D = tuple[float, float, float]


class HarnessWire(Component):
    fit_check = True

    def __init__(
        self, wire: WireDefinition, route: tuple[Point3D, ...], mates: tuple[str, ...]
    ) -> None:
        super().__init__(f"Wire_{wire.connector}_{wire.cavity}")
        if (
            len(route) < 2
            or any(not all(math.isfinite(v) for v in point) for point in route)
            or any(math.dist(a, b) <= 0 for a, b in pairwise(route))
        ):
            raise ValueError("Wire route needs finite distinct waypoints")
        self.wire, self.route, self.mates = wire, route, mates
        if self.route_length_mm > wire.length_mm:
            raise ValueError(f"{self.reference}: route exceeds the wire cut length")

    @property
    def route_length_mm(self) -> float:
        return sum(math.dist(a, b) for a, b in pairwise(self.route))

    def build(
        self,
        collection: bpy.types.Collection,
        construction: bpy.types.Collection,
        palette: dict[str, bpy.types.Material],
    ) -> tuple[bpy.types.Object, ...]:
        import bpy

        from cad.harness.base.blender import materials, modeling
        from shared.components.harness import WIRE_OUTSIDE_DIAMETERS_MM

        curve = bpy.data.curves.new(self.reference, "CURVE")
        curve.dimensions = "3D"
        curve.bevel_depth = WIRE_OUTSIDE_DIAMETERS_MM[self.wire.gauge_awg] / 2
        curve.bevel_resolution = 3
        curve.use_fill_caps = True
        spline = curve.splines.new("POLY")
        spline.points.add(len(self.route) - 1)
        for point, position in zip(spline.points, self.route):
            point.co = (*position, 1)
        obj = bpy.data.objects.new(self.reference, curve)
        collection.objects.link(obj)
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.context.view_layer.objects.active = obj
        bpy.ops.object.convert(target="MESH")
        obj = modeling.active_object("sweeping harness conductor")
        colors = {
            "red": (0.65, 0.02, 0.02),
            "black": (0.01, 0.01, 0.01),
            "orange": (0.9, 0.2, 0.015),
            "white": (0.85, 0.85, 0.8),
            "yellow": (0.9, 0.65, 0.015),
            "blue": (0.025, 0.12, 0.7),
        }
        obj.data.materials.append(
            materials.solid(
                f"Wire {self.wire.colour}", (*colors[self.wire.colour], 1), 0.45
            )
        )
        obj["fit_mates"] = list(self.mates)
        obj["mating_points_mm"] = [*self.route[0], *self.route[-1]]
        obj["mating_radius_mm"] = WIRE_OUTSIDE_DIAMETERS_MM[self.wire.gauge_awg] * 1.5
        obj["physical_reference"] = self.reference
        obj["connector"] = self.wire.connector
        obj["cavity"] = self.wire.cavity
        obj["net"] = self.wire.net
        obj["cut_length_mm"] = self.wire.length_mm
        obj["route_length_mm"] = self.route_length_mm
        obj["service_slack_mm"] = self.wire.length_mm - self.route_length_mm
        obj["fidelity"] = (
            "proposed route envelope; remaining service slack and bend radii require physical dressing"
        )
        return (obj,)
