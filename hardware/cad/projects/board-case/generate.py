"""Generate the printable case that holds the board, the Pi and the panel.

One of the project's two printed parts. It carries a single PCB on a grid of
bosses, hangs the Raspberry Pi underneath it, presents twelve buttons and a
display through a face-up bezel at the front, and receives the tile plate in a
rebate over the playing area.

Geometry is built in assembly coordinates: the case floor sits at z = 0 and its
top face at `CASE_HEIGHT_MM`, so the assembly view can load this part and the
plate without moving either of them.
"""

import sys
from pathlib import Path

import bpy

PROJECT_DIR = Path(__file__).parent
CAD_ROOT = PROJECT_DIR.parents[1]
sys.path.insert(0, str(CAD_ROOT))
GENERATED = CAD_ROOT / "generated"
GENERATED.mkdir(parents=True, exist_ok=True)

from core import dimensions as shared
from core import (
    materials,
    modeling,
    presentation,
    validation,
)

NAME = "board-case"
OUTPUT_PATH = GENERATED / f"{NAME}.blend"
PART_NAME = "Printable_Board_Case"

FLOOR_VENT_COUNT = 5
FLOOR_VENT_PITCH_MM = 8.0


def add_case(
    printable: bpy.types.Collection,
    construction: bpy.types.Collection,
    case_material: bpy.types.Material,
) -> bpy.types.Object:
    case = modeling.rounded_box(
        PART_NAME,
        shared.CASE_OUTER_SIZE_MM,
        (0.0, shared.CASE_CENTER_OFFSET_Y_MM, shared.CASE_HEIGHT_MM / 2.0),
        shared.CASE_OUTER_RADIUS_MM,
        printable,
    )
    case.data.materials.append(case_material)
    case["purpose"] = "Single-PCB case with a face-up control bezel"

    _hollow_cavity(case, construction)
    _cut_plate_rebate(case, construction)
    _cut_panel_apertures(case, construction)
    _cut_rear_apertures(case, construction)
    _cut_side_slot(case, construction)
    _cut_floor_vents(case, construction)
    _add_support_bosses(case, construction)
    _cut_plate_screws(case, construction)
    return case


def _hollow_cavity(case: bpy.types.Object, construction: bpy.types.Collection) -> None:
    """Remove the interior, leaving a ledge for the plate to rest on.

    The cavity is inset from the playing area by the plate ledge rather than by
    the wall thickness, so the frame stays solid and the cavity ceiling needs no
    support to print.
    """
    cavity_height = (
        shared.CASE_HEIGHT_MM - shared.TILE_PLATE_THICKNESS_MM - shared.CASE_FLOOR_MM
    )
    cavity = modeling.rounded_box(
        "Cutter_Case_Cavity",
        (
            shared.PLAYING_SPAN_MM - 2.0 * shared.CASE_PLATE_LEDGE_MM,
            shared.PCB_SIZE_MM[1] - 2.0 * shared.CASE_PLATE_LEDGE_MM,
            cavity_height,
        ),
        (
            0.0,
            shared.CASE_CENTER_OFFSET_Y_MM,
            shared.CASE_FLOOR_MM + cavity_height / 2.0,
        ),
        1.5,
        construction,
    )
    modeling.boolean_apply(case, cavity, "DIFFERENCE")
    bpy.data.objects.remove(cavity, do_unlink=True)


def _cut_plate_rebate(
    case: bpy.types.Object, construction: bpy.types.Collection
) -> None:
    """Open the top over the playing area so the plate sits flush."""
    depth = shared.TILE_PLATE_REBATE_DEPTH_MM + shared.BOOLEAN_THROUGH_OVERLAP_MM
    rebate = modeling.rounded_box(
        "Cutter_Plate_Rebate",
        (shared.PLAYING_SPAN_MM, shared.PLAYING_SPAN_MM, depth),
        (
            0.0,
            0.0,
            shared.CASE_HEIGHT_MM
            - shared.TILE_PLATE_REBATE_DEPTH_MM
            + depth / 2.0
            - shared.BOOLEAN_THROUGH_OVERLAP_MM / 2.0,
        ),
        0.8,
        construction,
    )
    modeling.boolean_apply(case, rebate, "DIFFERENCE")
    bpy.data.objects.remove(rebate, do_unlink=True)


def _cut_panel_apertures(
    case: bpy.types.Object, construction: bpy.types.Collection
) -> None:
    """Button holes and the display window in the face-up bezel."""
    skin = shared.TILE_PLATE_THICKNESS_MM
    through_height = skin + 2.0 * shared.BOOLEAN_THROUGH_OVERLAP_MM
    through_z = shared.CASE_HEIGHT_MM - skin / 2.0
    modeling.cut_batch(
        case,
        [
            modeling.cylinder(
                f"Cutter_Button_{index:02d}",
                shared.PANEL_BUTTON_HOLE_DIAMETER_MM,
                through_height,
                (x, y, through_z),
                construction,
                vertices=32,
            )
            for index, (x, y) in enumerate(shared.PANEL_BUTTON_POSITIONS_MM)
        ],
        "Cutter_All_Button_Holes",
    )
    # The window sits inside the recess that holds the module, so the two
    # overlap and cannot share a batch.
    modeling.cut_batch(
        case,
        [
            modeling.rounded_box(
                "Cutter_Display_Window",
                (*shared.PANEL_OLED_WINDOW_MM, through_height),
                (*shared.PANEL_OLED_CENTER_MM, through_z),
                0.6,
                construction,
            )
        ],
        "Cutter_Display_Window_Batch",
    )
    recess_depth = shared.PANEL_OLED_RECESS_DEPTH_MM
    modeling.cut_batch(
        case,
        [
            modeling.rounded_box(
                "Cutter_Display_Recess",
                (
                    shared.PANEL_OLED_RECESS_MM[0],
                    shared.PANEL_OLED_RECESS_MM[1],
                    recess_depth + shared.BOOLEAN_RECESS_OVERLAP_MM,
                ),
                (
                    *shared.PANEL_OLED_CENTER_MM,
                    shared.CASE_HEIGHT_MM
                    - skin
                    + recess_depth / 2.0
                    - shared.BOOLEAN_RECESS_OVERLAP_MM / 2.0,
                ),
                0.8,
                construction,
            )
        ],
        "Cutter_Display_Recess_Batch",
    )


def _cut_rear_apertures(
    case: bpy.types.Object, construction: bpy.types.Collection
) -> None:
    """Power input on the back wall, clear of the playing surface."""
    wall_y = shared.PLAYING_SPAN_MM / 2.0 + shared.CASE_FRAME_WIDTH_MM
    depth = 2.0 * shared.CASE_FRAME_WIDTH_MM
    center_y = wall_y - depth / 2.0 + shared.BOOLEAN_THROUGH_OVERLAP_MM
    z = shared.CASE_REAR_APERTURE_CENTER_Z_MM

    jack = modeling.cylinder(
        "Cutter_Jack_Aperture",
        shared.CASE_JACK_APERTURE_DIAMETER_MM,
        depth,
        (shared.PCB_STRIP_PLACEMENTS_MM["J3"][0], center_y, z),
        construction,
        vertices=48,
    )
    jack.rotation_euler = (1.5707963267948966, 0.0, 0.0)
    rocker = modeling.rounded_box(
        "Cutter_Rocker_Aperture",
        (shared.CASE_ROCKER_APERTURE_MM[0], depth, shared.CASE_ROCKER_APERTURE_MM[1]),
        (shared.PCB_STRIP_PLACEMENTS_MM["SW13"][0], center_y, z),
        0.6,
        construction,
    )
    modeling.cut_batch(case, [jack, rocker], "Cutter_All_Rear_Apertures")


def _cut_side_slot(case: bpy.types.Object, construction: bpy.types.Collection) -> None:
    """A slot on the right wall reaches the Pi's memory card."""
    wall_x = shared.PLAYING_SPAN_MM / 2.0 + shared.CASE_FRAME_WIDTH_MM
    depth = 2.0 * shared.CASE_FRAME_WIDTH_MM
    slot = modeling.rounded_box(
        "Cutter_Card_Slot",
        (depth, shared.CASE_SD_SLOT_MM[0], shared.CASE_SD_SLOT_MM[1]),
        (
            wall_x - depth / 2.0 + shared.BOOLEAN_THROUGH_OVERLAP_MM,
            shared.PI_BAY_CENTER_MM[1],
            shared.CASE_FLOOR_MM + 6.0,
        ),
        0.6,
        construction,
    )
    modeling.cut_batch(case, [slot], "Cutter_Card_Slot_Combined")


def _cut_floor_vents(
    case: bpy.types.Object, construction: bpy.types.Collection
) -> None:
    """Slots under the Pi so it is not sealed inside a closed box."""
    height = shared.CASE_FLOOR_MM + 2.0 * shared.BOOLEAN_THROUGH_OVERLAP_MM
    first = -(FLOOR_VENT_COUNT - 1) / 2.0 * FLOOR_VENT_PITCH_MM
    cutters = [
        modeling.rounded_box(
            f"Cutter_Floor_Vent_{index}",
            (shared.CASE_VENT_SLOT_MM[0], shared.CASE_VENT_SLOT_MM[1], height),
            (
                shared.PI_BAY_CENTER_MM[0],
                shared.PI_BAY_CENTER_MM[1] + first + index * FLOOR_VENT_PITCH_MM,
                shared.CASE_FLOOR_MM / 2.0,
            ),
            0.8,
            construction,
        )
        for index in range(FLOOR_VENT_COUNT)
    ]
    modeling.cut_batch(case, cutters, "Cutter_All_Floor_Vents")


def _add_support_bosses(
    case: bpy.types.Object, construction: bpy.types.Collection
) -> None:
    """Bosses carry the board off the floor and stop a 320 mm panel flexing.

    They stand on the grid lines, where neither an LED nor a Hall sensor sits.
    """
    height = shared.PI_BAY_HEIGHT_MM
    bosses = [
        modeling.cylinder(
            f"Boss_PCB_Support_{index:02d}",
            shared.PCB_SUPPORT_BOSS_DIAMETER_MM,
            height,
            (x, y, shared.CASE_FLOOR_MM + height / 2.0),
            construction,
            vertices=32,
        )
        for index, (x, y) in enumerate(shared.PCB_SUPPORT_POSITIONS_MM)
    ]
    modeling.union_batch(case, bosses, "Boss_All_PCB_Supports")

    pilot_depth = shared.PCB_SUPPORT_PILOT_DEPTH_MM
    pilots = [
        modeling.cylinder(
            f"Cutter_Support_Pilot_{index:02d}",
            shared.PCB_SUPPORT_PILOT_DIAMETER_MM,
            pilot_depth + shared.BOOLEAN_RECESS_OVERLAP_MM,
            (
                x,
                y,
                shared.PCB_UNDERSIDE_Z_MM
                - pilot_depth / 2.0
                + shared.BOOLEAN_RECESS_OVERLAP_MM / 2.0,
            ),
            construction,
            vertices=24,
        )
        for index, (x, y) in enumerate(shared.PCB_SUPPORT_POSITIONS_MM)
    ]
    modeling.cut_batch(case, pilots, "Cutter_All_Support_Pilots")


def _cut_plate_screws(
    case: bpy.types.Object, construction: bpy.types.Collection
) -> None:
    """Blind pilots in the ledge for the screws that hold the plate down."""
    depth = shared.PCB_SUPPORT_PILOT_DEPTH_MM
    ledge_top = shared.CASE_HEIGHT_MM - shared.TILE_PLATE_THICKNESS_MM
    pilots = [
        modeling.cylinder(
            f"Cutter_Plate_Screw_{index}",
            shared.PCB_SUPPORT_PILOT_DIAMETER_MM,
            depth + shared.BOOLEAN_RECESS_OVERLAP_MM,
            (
                x,
                y,
                ledge_top - depth / 2.0 + shared.BOOLEAN_RECESS_OVERLAP_MM / 2.0,
            ),
            construction,
            vertices=24,
        )
        for index, (x, y) in enumerate(shared.TILE_PLATE_SCREW_POSITIONS_MM)
    ]
    modeling.cut_batch(case, pilots, "Cutter_All_Plate_Screw_Pilots")


def render_view() -> None:
    bpy.context.scene.render.filepath = str(GENERATED / f"{NAME}.png")
    bpy.ops.render.render(write_still=True)


def build() -> None:
    modeling.clear_scene()
    scene = presentation.configure_scene(
        "Printable Board Case",
        shared.BLENDER_SCALE_LENGTH,
        (1200, 900),
        (0.02, 0.025, 0.035, 1.0),
        0.28,
    )
    scene["design_status"] = "Printable prototype"
    scene["project_role"] = "Case for one PCB, the Pi and the control panel"
    scene["grid_rows"] = shared.GRID_COUNT
    scene["grid_columns"] = shared.GRID_COUNT
    scene["pcb_size_mm"] = f"{shared.PCB_SIZE_MM[0]:g} x {shared.PCB_SIZE_MM[1]:g}"
    scene["panel_button_count"] = shared.PANEL_BUTTON_COUNT
    scene["pcb_support_count"] = len(shared.PCB_SUPPORT_POSITIONS_MM)
    scene["host"] = "Raspberry Pi Zero 2 W, hung under the board"
    scene["reference_build_volume_mm"] = "420 x 420 x 420 print service"

    printable = modeling.new_collection("PRINTABLE_PART")
    construction = modeling.new_collection("CONSTRUCTION")
    studio = modeling.new_collection("PRESENTATION")
    case_material = materials.solid(
        "Graphite printable case", (0.035, 0.045, 0.05, 1.0), 0.32
    )
    floor_material = materials.solid("Studio floor", (0.025, 0.028, 0.03, 1.0), 0.48)

    case = add_case(printable, construction, case_material)
    construction.hide_render = True
    construction.hide_viewport = True
    presentation.add_studio(
        studio,
        floor_material,
        (1500.0, 1500.0),
        (330.0, -420.0, 320.0),
        (0.0, shared.CASE_CENTER_OFFSET_Y_MM, 6.0),
        56,
        presentation.BOARD_STUDIO_LIGHTS,
    )

    validation.validate_fdm_part(case, shared.REFERENCE_SERVICE_BUILD_VOLUME_MM)
    scene["case_volume_mm3"] = case["mesh_volume_mm3"]
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_PATH))
    render_view()
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
