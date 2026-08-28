"""Generate the independently printable universal tile lid."""

from pathlib import Path
import sys

import bpy
from mathutils import Vector


PROJECT_DIR = Path(__file__).parent
BLENDER_ROOT = PROJECT_DIR.parents[1]
sys.path.insert(0, str(BLENDER_ROOT))

import dimensions as shared  # noqa: E402
import materials  # noqa: E402
import modeling  # noqa: E402
import presentation  # noqa: E402
import validation  # noqa: E402


OUTPUT_PATH = PROJECT_DIR / "tile-top.blend"
RENDER_DIR = PROJECT_DIR / "renders"


def add_lid_rails(
    lid: bpy.types.Object,
    construction: bpy.types.Collection,
) -> None:
    outer_span = shared.TILE_LID_RAIL_OUTER_SPAN_MM
    inner_span = shared.TILE_LID_RAIL_INNER_SPAN_MM
    rail_z = (
        shared.TILE_BOTTOM_HEIGHT_MM
        - shared.TILE_LID_RAIL_DEPTH_MM / 2.0
        + shared.TILE_LID_RAIL_OVERLAP_MM
    )
    rail_offset = (outer_span - shared.TILE_LID_RAIL_WIDTH_MM) / 2.0
    rails = (
        (
            "Rail_North",
            (outer_span, shared.TILE_LID_RAIL_WIDTH_MM, shared.TILE_LID_RAIL_DEPTH_MM),
            (0.0, rail_offset, rail_z),
        ),
        (
            "Rail_South",
            (outer_span, shared.TILE_LID_RAIL_WIDTH_MM, shared.TILE_LID_RAIL_DEPTH_MM),
            (0.0, -rail_offset, rail_z),
        ),
        (
            "Rail_East",
            (shared.TILE_LID_RAIL_WIDTH_MM, inner_span, shared.TILE_LID_RAIL_DEPTH_MM),
            (rail_offset, 0.0, rail_z),
        ),
        (
            "Rail_West",
            (shared.TILE_LID_RAIL_WIDTH_MM, inner_span, shared.TILE_LID_RAIL_DEPTH_MM),
            (-rail_offset, 0.0, rail_z),
        ),
    )
    for name, dimensions, location in rails:
        rail = modeling.rounded_box(
            name, dimensions, location, 0.2, construction
        )
        modeling.boolean_apply(lid, rail, "UNION")
        bpy.data.objects.remove(rail, do_unlink=True)


def build_lid(
    printable: bpy.types.Collection,
    cutters: bpy.types.Collection,
    construction: bpy.types.Collection,
    material: bpy.types.Material,
) -> tuple[bpy.types.Object, tuple[bpy.types.Object, ...]]:
    lid = modeling.rounded_box(
        "Tile_Top_Lid",
        shared.TILE_TOP_BASE_SIZE_MM,
        (
            0.0,
            0.0,
            shared.TILE_BOTTOM_HEIGHT_MM + shared.TILE_TOP_THICKNESS_MM / 2.0,
        ),
        shared.TILE_OUTER_RADIUS_MM,
        printable,
    )
    lid.data.materials.append(material)
    lid_cutters = (
        modeling.rounded_box(
            "Cutter_LED_Light_Aperture",
            (
                *shared.LED_APERTURE_MM,
                shared.TILE_TOP_THICKNESS_MM
                + 2.0 * shared.TILE_BOOLEAN_THROUGH_OVERLAP_MM,
            ),
            (
                *shared.LED_POSITION_MM,
                shared.TILE_BOTTOM_HEIGHT_MM + shared.TILE_TOP_THICKNESS_MM / 2.0,
            ),
            0.65,
            cutters,
        ),
        modeling.rounded_box(
            "Cutter_LED_Underside_Pocket",
            (
                *shared.LED_POCKET_MM[:2],
                shared.LED_POCKET_MM[2]
                + 2.0 * shared.TILE_BOOLEAN_RECESS_OVERLAP_MM,
            ),
            (
                *shared.LED_POSITION_MM,
                shared.TILE_BOTTOM_HEIGHT_MM
                + shared.LED_POCKET_MM[2] / 2.0
                - shared.TILE_BOOLEAN_RECESS_OVERLAP_MM,
            ),
            0.8,
            cutters,
        ),
        modeling.annular_cutter(
            "Cutter_Hidden_Magnet_Ring_Recess",
            shared.MAGNET_RING_OUTER_DIAMETER_MM,
            shared.MAGNET_RING_INNER_DIAMETER_MM,
            shared.TILE_BOTTOM_HEIGHT_MM - shared.TILE_BOOLEAN_RECESS_OVERLAP_MM,
            shared.TILE_BOTTOM_HEIGHT_MM + shared.MAGNET_RING_DEPTH_MM,
            cutters,
        ),
    )
    for cutter in lid_cutters:
        modeling.boolean_apply(lid, cutter, "DIFFERENCE")
    add_lid_rails(lid, construction)
    return lid, lid_cutters


def render(lid: bpy.types.Object) -> None:
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    camera = bpy.data.objects["Camera_Render"]
    camera.location = (48.0, -48.0, 52.0)
    camera.data.lens = 55
    modeling.point_at(camera, Vector((0.0, 0.0, 3.0)))
    bpy.context.scene.render.filepath = str(RENDER_DIR / "top.png")
    bpy.ops.render.render(write_still=True)


def build() -> None:
    modeling.clear_scene()
    scene = presentation.configure_scene(
        "Printable Universal Tile Lid",
        shared.BLENDER_SCALE_LENGTH,
        (900, 900),
        (0.025, 0.03, 0.04, 1.0),
        0.35,
    )
    scene["project_role"] = "One independently printable part"
    scene["part_name"] = "Tile_Top_Lid"
    scene["intended_quantity"] = 64
    scene["led_package_reference"] = shared.LED_PACKAGE_REFERENCE

    printable = modeling.new_collection("PRINTABLE_PART")
    cutters = modeling.new_collection("DESIGN_CUTTERS")
    construction = modeling.new_collection("CONSTRUCTION")
    studio = modeling.new_collection("PRESENTATION")
    lid_material = materials.wood(
        "Maple tile lid",
        (0.42, 0.20, 0.065, 1.0),
        (0.19, 0.065, 0.018, 1.0),
    )
    floor_material = materials.solid(
        "Studio floor", (0.025, 0.028, 0.03, 1.0), 0.48
    )
    lid, lid_cutters = build_lid(printable, cutters, construction, lid_material)
    for cutter in lid_cutters:
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

    validation.validate_fdm_part(lid, shared.REFERENCE_COMPACT_BUILD_VOLUME_MM)
    scene["part_volume_mm3"] = lid["mesh_volume_mm3"]
    lid.select_set(True)
    bpy.context.view_layer.objects.active = lid
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_PATH))
    render(lid)
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
