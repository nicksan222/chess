"""Generate the empty printable board tray that receives 64 removable tiles."""

from pathlib import Path
import sys

import bpy


PROJECT_DIR = Path(__file__).parent
BLENDER_ROOT = PROJECT_DIR.parent
sys.path.insert(0, str(BLENDER_ROOT))

import dimensions as shared  # noqa: E402
import materials  # noqa: E402
import modeling  # noqa: E402
import presentation  # noqa: E402
import validation  # noqa: E402


OUTPUT_PATH = PROJECT_DIR / "board-skeleton.blend"
RENDER_DIR = PROJECT_DIR / "renders"


def add_empty_board(
    printable: bpy.types.Collection,
    construction: bpy.types.Collection,
    board_material: bpy.types.Material,
) -> bpy.types.Object:
    board = modeling.rounded_box(
        "Printable_Empty_Board_Tray",
        shared.BOARD_TRAY_OUTER_SIZE_MM,
        (0.0, 0.0, shared.BOARD_HEIGHT_MM / 2.0),
        2.2,
        printable,
    )
    board.data.materials.append(board_material)
    board["purpose"] = "Rail-free printable tray for 64 Velcro-mounted tiles"

    cavity_depth = shared.BOARD_TRAY_CAVITY_SIZE_MM[2]
    cavity = modeling.rounded_box(
        "Cutter_Empty_Tile_Area",
        (
            shared.BOARD_TRAY_CAVITY_SIZE_MM[0],
            shared.BOARD_TRAY_CAVITY_SIZE_MM[1],
            cavity_depth + 0.6,
        ),
        (
            0.0,
            0.0,
            shared.BOARD_FLOOR_THICKNESS_MM + cavity_depth / 2.0 + 0.2,
        ),
        1.0,
        construction,
    )
    modeling.boolean_apply(board, cavity, "DIFFERENCE")
    bpy.data.objects.remove(cavity, do_unlink=True)

    pilot_height = (
        shared.BOARD_MOUNT_SCREW_PILOT_DEPTH_MM
        + 2.0 * shared.TILE_BOOLEAN_RECESS_OVERLAP_MM
    )
    pilot_z = (
        shared.BOARD_FLOOR_THICKNESS_MM
        - shared.BOARD_MOUNT_SCREW_PILOT_DEPTH_MM / 2.0
        + shared.TILE_BOOLEAN_RECESS_OVERLAP_MM / 2.0
    )
    pilot_cutters = [
        modeling.cylinder(
            f"Cutter_Screw_Pilot_{row:02d}_{column:02d}_{screw_index}",
            shared.BOARD_MOUNT_SCREW_PILOT_DIAMETER_MM,
            pilot_height,
            (x, y, pilot_z),
            construction,
            vertices=48,
        )
        for row, column, screw_index, x, y in (
            shared.BOARD_MOUNT_SCREW_PILOT_POSITIONS_MM
        )
    ]
    bpy.ops.object.select_all(action="DESELECT")
    for cutter in pilot_cutters:
        cutter.select_set(True)
    bpy.context.view_layer.objects.active = pilot_cutters[0]
    bpy.ops.object.join()
    combined_pilots = bpy.context.object
    combined_pilots.name = "Cutter_All_Optional_Screw_Pilots"
    modeling.boolean_apply(board, combined_pilots, "DIFFERENCE")
    bpy.data.objects.remove(combined_pilots, do_unlink=True)
    return board


def render_view() -> None:
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    bpy.context.scene.render.filepath = str(RENDER_DIR / "skeleton.png")
    bpy.ops.render.render(write_still=True)


def build() -> None:
    modeling.clear_scene()
    scene = presentation.configure_scene(
        "Empty Printable Tile Board",
        shared.BLENDER_SCALE_LENGTH,
        (1200, 900),
        (0.02, 0.025, 0.035, 1.0),
        0.28,
    )
    scene["design_status"] = "Printable prototype"
    scene["project_role"] = "Empty board tray; printable tiles are separate parts"
    scene["grid_rows"] = shared.GRID_COUNT
    scene["grid_columns"] = shared.GRID_COUNT
    scene["tile_count"] = 0
    scene["intended_tile_quantity"] = 64
    scene["primary_mount"] = "Velcro on flat tray floor"
    scene["alternate_mount"] = "Blind pilot holes for optional screws"
    scene["reference_build_volume_mm"] = "360 x 360 x 360"

    printable = modeling.new_collection("PRINTABLE_BOARD_PARTS")
    construction = modeling.new_collection("CONSTRUCTION")
    studio = modeling.new_collection("PRESENTATION")
    board_material = materials.solid(
        "Graphite printable board", (0.035, 0.045, 0.05, 1.0), 0.32
    )
    floor_material = materials.solid(
        "Studio floor", (0.025, 0.028, 0.03, 1.0), 0.48
    )
    board = add_empty_board(printable, construction, board_material)
    construction.hide_render = True
    construction.hide_viewport = True
    presentation.add_studio(
        studio,
        floor_material,
        (1400.0, 1400.0),
        (310.0, -370.0, 300.0),
        (0.0, 0.0, 4.0),
        58,
        presentation.BOARD_STUDIO_LIGHTS,
    )

    validation.validate_fdm_part(board, shared.REFERENCE_LARGE_BUILD_VOLUME_MM)
    scene["board_volume_mm3"] = board["mesh_volume_mm3"]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_PATH))
    render_view()
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
