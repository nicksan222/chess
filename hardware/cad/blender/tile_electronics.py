"""Reusable single-tile electronics and tidy harness presentation references."""

from math import pi

import bpy

import dimensions as shared
import materials
import modeling


def wire_curve(
    name: str,
    points: tuple[tuple[float, float, float], ...],
    material: bpy.types.Material,
    collection: bpy.types.Collection,
) -> bpy.types.Object:
    curve_data = bpy.data.curves.new(name=f"{name}_Curve", type="CURVE")
    curve_data.dimensions = "3D"
    curve_data.resolution_u = 2
    curve_data.bevel_depth = shared.ELECTRONICS_WIRE_DIAMETER_MM / 2.0
    curve_data.bevel_resolution = 3
    spline = curve_data.splines.new(type="BEZIER")
    spline.bezier_points.add(len(points) - 1)
    for point, coordinate in zip(spline.bezier_points, points):
        point.co = coordinate
        point.handle_left_type = "AUTO"
        point.handle_right_type = "AUTO"
    wire = bpy.data.objects.new(name, curve_data)
    collection.objects.link(wire)
    wire.data.materials.append(material)
    wire["purpose"] = "Flexible insulated hookup wire reference"
    return wire


def create_materials() -> dict[str, bpy.types.Material]:
    return {
        "pcb": materials.solid("LED carrier PCB", (0.02, 0.18, 0.07, 1.0), 0.36),
        "body": materials.solid(
            "Electronic component body", (0.82, 0.84, 0.80, 1.0), 0.3
        ),
        "emitter": materials.solid(
            "RGB emitter window", (0.7, 0.82, 0.9, 1.0), 0.12
        ),
        "glass": materials.solid(
            "Reed glass capsule", (0.28, 0.55, 0.62, 1.0), 0.12
        ),
        "metal": materials.solid(
            "Tinned component leads", (0.42, 0.46, 0.48, 1.0), 0.22, 0.86
        ),
        "red": materials.solid("Wire 5V red", (0.55, 0.018, 0.012, 1.0), 0.5),
        "black": materials.solid(
            "Wire ground black", (0.012, 0.014, 0.016, 1.0), 0.58
        ),
        "green": materials.solid(
            "Wire data in green", (0.02, 0.34, 0.08, 1.0), 0.5
        ),
        "blue": materials.solid(
            "Wire data out blue", (0.015, 0.12, 0.55, 1.0), 0.5
        ),
        "yellow": materials.solid(
            "Wire reed row yellow", (0.8, 0.48, 0.02, 1.0), 0.5
        ),
        "orange": materials.solid(
            "Wire reed column orange", (0.8, 0.16, 0.015, 1.0), 0.5
        ),
    }


def add_wired_electronics(collection: bpy.types.Collection) -> None:
    component_materials = create_materials()
    led_position = shared.LED_POSITION_MM
    bottom_height = shared.TILE_BOTTOM_HEIGHT_MM

    pcb_z = bottom_height - shared.LED_BREAKOUT_PCB_MM[2] / 2.0
    pcb = modeling.rounded_box(
        "LED_Breakout_PCB",
        shared.LED_BREAKOUT_PCB_MM,
        (*led_position, pcb_z),
        0.45,
        collection,
    )
    pcb.data.materials.append(component_materials["pcb"])
    pcb["purpose"] = "Small per-tile addressable LED carrier PCB reference"

    led_z = bottom_height + shared.LED_PACKAGE_NOMINAL_SIZE_MM[2] / 2.0
    led = modeling.rounded_box(
        "WS2812B_Compatible_5050_LED",
        shared.LED_PACKAGE_NOMINAL_SIZE_MM,
        (*led_position, led_z),
        0.35,
        collection,
    )
    led.data.materials.append(component_materials["body"])
    led["reference"] = shared.LED_PACKAGE_REFERENCE
    emitter = modeling.cylinder(
        "RGB_LED_Emitter_Window",
        shared.LED_EMITTER_WINDOW_MM[0],
        0.22,
        (
            *led_position,
            bottom_height + shared.LED_PACKAGE_NOMINAL_SIZE_MM[2] + 0.02,
        ),
        collection,
    )
    emitter.data.materials.append(component_materials["emitter"])

    capacitor = modeling.rounded_box(
        "LED_Decoupling_Capacitor",
        (2.0, 1.25, 0.8),
        (10.0, 10.0, bottom_height - shared.LED_BREAKOUT_PCB_MM[2] - 0.4),
        0.18,
        collection,
    )
    capacitor.data.materials.append(component_materials["body"])
    capacitor["purpose"] = "Per-pixel decoupling capacitor reference"

    reed_z = 4.0
    reed = modeling.cylinder(
        "Central_Glass_Reed_Sensor",
        shared.REED_SENSOR_BODY_MM[1],
        shared.REED_SENSOR_BODY_MM[0],
        (*shared.REED_SENSOR_POSITION_MM, reed_z),
        collection,
    )
    reed.rotation_euler[0] = pi / 2.0
    reed.data.materials.append(component_materials["glass"])
    reed["purpose"] = "Normally-open magnetic piece sensor reference"
    for side in (-1.0, 1.0):
        lead = modeling.cylinder(
            f"Reed_Lead_{'South' if side < 0 else 'North'}",
            0.45,
            5.0,
            (0.0, side * 9.5, reed_z),
            collection,
        )
        lead.rotation_euler[0] = pi / 2.0
        lead.data.materials.append(component_materials["metal"])

    input_specs = (
        ("LED_5V_In", "red", -1.0, 11.5),
        ("LED_Ground_In", "black", 0.0, 13.0),
        ("LED_Data_In", "green", 1.0, 14.5),
    )
    for name, color, offset, endpoint_y in input_specs:
        port_y = offset * 1.1
        lane_y = -7.2 + offset * 1.1
        lane_x = 7.2 + offset * 1.1
        wire_curve(
            name,
            (
                (-22.0, port_y, 3.0),
                (-17.8, port_y, 3.0),
                (-14.8, lane_y, 3.35),
                (lane_x, lane_y, 3.35),
                (lane_x, 7.4, 3.8),
                (8.7, endpoint_y, 4.8),
            ),
            component_materials[color],
            collection,
        )

    output_specs = (
        ("LED_5V_Out", "red", -1.0, 11.5),
        ("LED_Ground_Out", "black", 0.0, 13.0),
        ("LED_Data_Out", "blue", 1.0, 14.5),
    )
    for name, color, offset, endpoint_y in output_specs:
        lane_x = 14.5 + offset
        port_y = offset * 1.1
        wire_curve(
            name,
            (
                (17.3, endpoint_y, 4.8),
                (lane_x, 8.0, 4.0),
                (lane_x, 4.2, 3.5),
                (17.8, port_y, 3.0),
                (22.0, port_y, 3.0),
            ),
            component_materials[color],
            collection,
        )

    for name, size, location in (
        ("Input_Harness_Clip", (1.2, 4.4, 0.7), (-5.0, -7.2, 3.7)),
        ("Output_Harness_Clip", (4.2, 1.2, 0.7), (14.5, 5.8, 3.9)),
    ):
        clip = modeling.rounded_box(name, size, location, 0.28, collection)
        clip.data.materials.append(component_materials["black"])
        clip["purpose"] = "Printed or adhesive wire-harness restraint reference"

    wire_curve(
        "Reed_Row_Wire",
        ((0.0, 12.0, reed_z), (0.0, 17.8, 3.0), (0.0, 22.0, 3.0)),
        component_materials["yellow"],
        collection,
    )
    wire_curve(
        "Reed_Column_Wire",
        ((0.0, -12.0, reed_z), (0.0, -17.8, 3.0), (0.0, -22.0, 3.0)),
        component_materials["orange"],
        collection,
    )
