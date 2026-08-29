"""Generate the independently printable universal tile wiring tray."""

from pathlib import Path
import sys

import bpy
from mathutils import Vector


PROJECT_DIR = Path(__file__).parent
CAD_ROOT = PROJECT_DIR.parents[1]
sys.path.insert(0, str(CAD_ROOT))
GENERATED = CAD_ROOT / "generated"
GENERATED.mkdir(parents=True, exist_ok=True)

from core import dimensions as shared  # noqa: E402
from core import materials  # noqa: E402
from core import modeling  # noqa: E402
from core import presentation  # noqa: E402
from core import validation  # noqa: E402


NAME = "single-tile-bottom"
OUTPUT_PATH = GENERATED / f"{NAME}.blend"


def add_optional_screw_mounts(
    tray: bpy.types.Object,
    cutters: bpy.types.Collection,
    construction: bpy.types.Collection,
) -> tuple[bpy.types.Object, ...]:
    screw_cutters = []
    for index, position in enumerate(shared.TILE_MOUNT_SCREW_POSITIONS_MM):
        boss = modeling.cylinder(
            f"Screw_Boss_{index}",
            shared.TILE_MOUNT_SCREW_BOSS_DIAMETER_MM,
            shared.TILE_MOUNT_SCREW_BOSS_HEIGHT_MM,
            (*position, shared.TILE_MOUNT_SCREW_BOSS_HEIGHT_MM / 2.0),
            construction,
        )
        modeling.boolean_apply(tray, boss, "UNION")
        bpy.data.objects.remove(boss, do_unlink=True)

        head_recess = modeling.cylinder(
            f"Cutter_Mount_Screw_Head_{index}",
            shared.TILE_MOUNT_SCREW_HEAD_DIAMETER_MM,
            shared.TILE_MOUNT_SCREW_HEAD_DEPTH_MM
            + shared.TILE_BOOLEAN_RECESS_OVERLAP_MM,
            (
                *position,
                shared.TILE_MOUNT_SCREW_BOSS_HEIGHT_MM
                - shared.TILE_MOUNT_SCREW_HEAD_DEPTH_MM / 2.0
                + shared.TILE_BOOLEAN_RECESS_OVERLAP_MM / 2.0,
            ),
            cutters,
        )
        through_hole = modeling.cylinder(
            f"Cutter_Mount_Screw_Through_{index}",
            shared.TILE_MOUNT_SCREW_CLEARANCE_DIAMETER_MM,
            shared.TILE_MOUNT_SCREW_BOSS_HEIGHT_MM
            + 2.0 * shared.TILE_BOOLEAN_THROUGH_OVERLAP_MM,
            (*position, shared.TILE_MOUNT_SCREW_BOSS_HEIGHT_MM / 2.0),
            cutters,
        )
        for cutter in (head_recess, through_hole):
            modeling.boolean_apply(tray, cutter, "DIFFERENCE")
            screw_cutters.append(cutter)
    return tuple(screw_cutters)


def build_tray(
    printable: bpy.types.Collection,
    cutters: bpy.types.Collection,
    construction: bpy.types.Collection,
    material: bpy.types.Material,
) -> tuple[bpy.types.Object, tuple[bpy.types.Object, ...]]:
    tray = modeling.rounded_box(
        "Tile_Bottom_Tray",
        shared.TILE_BOTTOM_BASE_SIZE_MM,
        (0.0, 0.0, shared.TILE_BOTTOM_HEIGHT_MM / 2.0),
        shared.TILE_OUTER_RADIUS_MM,
        printable,
    )
    tray.data.materials.append(material)
    cavity_size = shared.TILE_INTERNAL_CAVITY_SIZE_MM
    base_cutters = [
        modeling.rounded_box(
            "Cutter_Internal_Wiring_Cavity",
            (
                cavity_size,
                cavity_size,
                shared.TILE_BOTTOM_HEIGHT_MM - shared.TILE_BOTTOM_FLOOR_MM,
            ),
            (
                0.0,
                0.0,
                shared.TILE_BOTTOM_FLOOR_MM
                + (
                    shared.TILE_BOTTOM_HEIGHT_MM - shared.TILE_BOTTOM_FLOOR_MM
                )
                / 2.0
                + shared.TILE_BOOLEAN_RECESS_OVERLAP_MM,
            ),
            1.0,
            cutters,
        ),
        modeling.rounded_box(
            "Cutter_Lid_Rebate",
            (
                shared.TILE_SIZE_MM - 2.0 * shared.TILE_LID_REBATE_EDGE_MM,
                shared.TILE_SIZE_MM - 2.0 * shared.TILE_LID_REBATE_EDGE_MM,
                shared.TILE_LID_REBATE_HEIGHT_MM,
            ),
            (0.0, 0.0, shared.TILE_LID_REBATE_CENTER_Z_MM),
            0.7,
            cutters,
        ),
    ]
    for name, dimensions, location in (
        (
            "Cutter_Wire_Port_East",
            (
                shared.TILE_WIRE_PORT_CUTTER_DEPTH_MM,
                shared.TILE_WIRE_PORT_WIDTH_MM,
                shared.TILE_WIRE_PORT_HEIGHT_MM,
            ),
            (
                shared.TILE_WIRE_PORT_CUTTER_OFFSET_MM,
                0.0,
                shared.TILE_WIRE_PORT_CENTER_Z_MM,
            ),
        ),
        (
            "Cutter_Wire_Port_West",
            (
                shared.TILE_WIRE_PORT_CUTTER_DEPTH_MM,
                shared.TILE_WIRE_PORT_WIDTH_MM,
                shared.TILE_WIRE_PORT_HEIGHT_MM,
            ),
            (
                -shared.TILE_WIRE_PORT_CUTTER_OFFSET_MM,
                0.0,
                shared.TILE_WIRE_PORT_CENTER_Z_MM,
            ),
        ),
        (
            "Cutter_Wire_Port_North",
            (
                shared.TILE_WIRE_PORT_WIDTH_MM,
                shared.TILE_WIRE_PORT_CUTTER_DEPTH_MM,
                shared.TILE_WIRE_PORT_HEIGHT_MM,
            ),
            (
                0.0,
                shared.TILE_WIRE_PORT_CUTTER_OFFSET_MM,
                shared.TILE_WIRE_PORT_CENTER_Z_MM,
            ),
        ),
        (
            "Cutter_Wire_Port_South",
            (
                shared.TILE_WIRE_PORT_WIDTH_MM,
                shared.TILE_WIRE_PORT_CUTTER_DEPTH_MM,
                shared.TILE_WIRE_PORT_HEIGHT_MM,
            ),
            (
                0.0,
                -shared.TILE_WIRE_PORT_CUTTER_OFFSET_MM,
                shared.TILE_WIRE_PORT_CENTER_Z_MM,
            ),
        ),
    ):
        base_cutters.append(
            modeling.rounded_box(name, dimensions, location, 0.5, cutters)
        )
    for index, position in enumerate(shared.TILE_VELCRO_PAD_POSITIONS_MM):
        base_cutters.append(
            modeling.rounded_box(
                f"Cutter_Velcro_Pad_Pocket_{index}",
                (
                    *shared.TILE_VELCRO_PAD_SIZE_MM,
                    shared.TILE_VELCRO_PAD_DEPTH_MM
                    + shared.TILE_BOOLEAN_RECESS_OVERLAP_MM,
                ),
                (
                    *position,
                    (
                        shared.TILE_VELCRO_PAD_DEPTH_MM
                        - shared.TILE_BOOLEAN_RECESS_OVERLAP_MM
                    )
                    / 2.0,
                ),
                shared.TILE_VELCRO_PAD_RADIUS_MM,
                cutters,
            )
        )
    for cutter in base_cutters:
        modeling.boolean_apply(tray, cutter, "DIFFERENCE")
    all_cutters = tuple(base_cutters) + add_optional_screw_mounts(
        tray, cutters, construction
    )
    return tray, all_cutters


def render(tray: bpy.types.Object) -> None:
    scene = bpy.context.scene
    camera = bpy.data.objects["Camera_Render"]
    floor = bpy.data.objects["Studio_Floor"]
    camera.location = (52.0, -52.0, -36.0)
    camera.data.lens = 55
    modeling.point_at(camera, Vector((0.0, 0.0, 3.0)))
    floor.hide_render = True
    scene.render.filepath = str(GENERATED / f"{NAME}.png")
    bpy.ops.render.render(write_still=True)
    floor.hide_render = False


def build() -> None:
    modeling.clear_scene()
    scene = presentation.configure_scene(
        "Printable Universal Tile Tray",
        shared.BLENDER_SCALE_LENGTH,
        (900, 900),
        (0.025, 0.03, 0.04, 1.0),
        0.35,
    )
    scene["project_role"] = "One independently printable part"
    scene["part_name"] = "Tile_Bottom_Tray"
    scene["intended_quantity"] = 64
    scene["board_mount_primary"] = "Four adhesive-backed hook-and-loop pads"
    scene["board_mount_alternative"] = "Two lid-accessible screws"

    printable = modeling.new_collection("PRINTABLE_PART")
    cutters = modeling.new_collection("DESIGN_CUTTERS")
    construction = modeling.new_collection("CONSTRUCTION")
    studio = modeling.new_collection("PRESENTATION")
    tray_material = materials.solid(
        "Graphite polymer tray", (0.025, 0.035, 0.04, 1.0), 0.3
    )
    floor_material = materials.solid(
        "Studio floor", (0.025, 0.028, 0.03, 1.0), 0.48
    )
    tray, tray_cutters = build_tray(
        printable, cutters, construction, tray_material
    )
    for cutter in tray_cutters:
        cutter.display_type = "WIRE"
        cutter.color = (0.85, 0.18, 0.12, 1.0)
        cutter.hide_render = True
    cutters.hide_render = True
    cutters.hide_viewport = True
    construction.hide_render = True
    construction.hide_viewport = True
    presentation.add_studio(
        studio,
        floor_material,
        (400.0, 400.0),
        (48.0, -48.0, 52.0),
        (0.0, 0.0, 3.0),
        55,
        presentation.TILE_STUDIO_LIGHTS,
    )

    validation.validate_fdm_part(tray, shared.REFERENCE_COMPACT_BUILD_VOLUME_MM)
    scene["part_volume_mm3"] = tray["mesh_volume_mm3"]
    tray.select_set(True)
    bpy.context.view_layer.objects.active = tray
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_PATH))
    render(tray)
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
