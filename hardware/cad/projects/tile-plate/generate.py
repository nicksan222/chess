"""Generate the single printable tile plate: checkerboard and control bezel.

The second of the project's two printed parts. Revision A printed 64 separate
two-part tiles; this replaces all 128 of those prints with one overlay that
covers the whole PCB and drops into a rebate on the case rim. Over the control
strip it is the bezel: button holes, and the display window and recess.

Geometry is built in assembly coordinates: the plate occupies the top
`TILE_PLATE_THICKNESS_MM` of the case, so the assembly view can load it and the
case without moving either of them.

Pipeline: `build()` makes the scene, `add_plate()` creates a rounded slab and applies
the cut stages below in turn, `project.save_printable()` validates, saves and renders.
All sizes come from `shared` (`hardware/shared/dimensions/`); none are repeated here.
Cutter objects live in the hidden CONSTRUCTION collection. Cutters are batched with
`modeling.cut_batch`, whose members must not overlap one another.
"""

import sys
from dataclasses import dataclass
from pathlib import Path

import bpy

PROJECT_DIR = Path(__file__).parent
CAD_ROOT = PROJECT_DIR.parents[1]
sys.path.insert(0, str(CAD_ROOT))
GENERATED = CAD_ROOT / "generated"

from core import dimensions as shared
from core import (
    materials,
    modeling,
    presentation,
    project,
)

# Project name: output file stem (`tile-plate.blend`) and the directory name.
NAME = "tile-plate"
# Object name other projects (`board-assembly`) import from the .blend; keep stable.
PART_NAME = "Printable_Tile_Plate"

# Assembly coordinates: the plate's top face is flush with the case height and its
# underside is one plate thickness lower, so the case and plate meet without moving.
TOP_Z_MM = shared.CASE_HEIGHT_MM
UNDERSIDE_Z_MM = shared.CASE_HEIGHT_MM - shared.TILE_PLATE_THICKNESS_MM


@dataclass(frozen=True, slots=True)
class TilePlateMetadata:
    """Facts stored as custom properties on the scene (visible in the saved .blend)."""

    design_status: str
    project_role: str
    grid_rows: int
    grid_columns: int
    square_count: int
    dark_square_count: int
    diffuser_skin_mm: float
    panel_button_count: int
    reference_build_volume_mm: str

    def apply_to(self, scene: bpy.types.Scene) -> None:
        project.set_scene_property(scene, "design_status", self.design_status)
        project.set_scene_property(scene, "project_role", self.project_role)
        project.set_scene_property(scene, "grid_rows", self.grid_rows)
        project.set_scene_property(scene, "grid_columns", self.grid_columns)
        project.set_scene_property(scene, "square_count", self.square_count)
        project.set_scene_property(scene, "dark_square_count", self.dark_square_count)
        project.set_scene_property(scene, "diffuser_skin_mm", self.diffuser_skin_mm)
        project.set_scene_property(scene, "panel_button_count", self.panel_button_count)
        project.set_scene_property(
            scene, "reference_build_volume_mm", self.reference_build_volume_mm
        )


def add_plate(
    printable: bpy.types.Collection,
    construction: bpy.types.Collection,
    plate_material: bpy.types.Material,
) -> bpy.types.Object:
    """Build the plate: a slab, then each feature cut in turn.

    The slab is centred on the plate's own offset (the plate covers the control strip
    too, so it is not centred on the playing area) and bevelled 0.8 mm.
    """
    plate = modeling.rounded_box(
        PART_NAME,
        shared.TILE_PLATE_SIZE_MM,
        (
            0.0,
            shared.TILE_PLATE_CENTER_Y_MM,
            UNDERSIDE_Z_MM + shared.TILE_PLATE_THICKNESS_MM / 2.0,
        ),
        0.8,
        printable,
    )
    plate.data.materials.append(plate_material)
    plate["purpose"] = "Single overlay carrying all 64 squares and the bezel"

    # Underside pockets, top-face engraving, then screws and the bezel openings.
    _cut_underside_pockets(plate, construction)
    _cut_led_pockets(plate, construction)
    _cut_grid_grooves(plate, construction)
    _cut_dark_squares(plate, construction)
    _cut_screws(plate, construction)
    _cut_bezel(plate, construction)
    return plate


def _cut_underside_pockets(
    plate: bpy.types.Object, construction: bpy.types.Collection
) -> None:
    """One pocket per square: removes weight and clears the Hall sensors.

    Pockets sit on the square grid and leave ribs on the grid lines. They overshoot
    the underside by `BOOLEAN_RECESS_OVERLAP_MM` so the cutter face is not coplanar
    with the plate face (coplanar faces defeat the exact solver).
    """
    depth = shared.TILE_PLATE_UNDERSIDE_POCKET_DEPTH_MM
    half_span = shared.TILE_PLATE_UNDERSIDE_POCKET_SPAN_MM / 2.0
    z0 = UNDERSIDE_Z_MM - shared.BOOLEAN_RECESS_OVERLAP_MM
    z1 = UNDERSIDE_Z_MM + depth
    cutters = [
        modeling.box_between(
            f"Cutter_Underside_Pocket_{square.row:02d}_{square.column:02d}",
            (
                square.centre_mm[0] - half_span,
                square.centre_mm[0] + half_span,
                square.centre_mm[1] - half_span,
                square.centre_mm[1] + half_span,
                z0,
                z1,
            ),
            construction,
        )
        for square in shared.BOARD_SQUARES
    ]
    modeling.cut_batch(plate, cutters, "Cutter_All_Underside_Pockets")


def _cut_led_pockets(
    plate: bpy.types.Object, construction: bpy.types.Collection
) -> None:
    """A deeper pocket over each LED, leaving a thin diffusing skin.

    The pocket is centred on the LED position (not the square centre) from the shared
    LED offset; the material above it is what diffuses the light.
    """
    depth = shared.TILE_PLATE_LED_POCKET_MM[2]
    half_x = shared.TILE_PLATE_LED_POCKET_MM[0] / 2.0
    half_y = shared.TILE_PLATE_LED_POCKET_MM[1] / 2.0
    z0 = UNDERSIDE_Z_MM - shared.BOOLEAN_RECESS_OVERLAP_MM
    z1 = UNDERSIDE_Z_MM + depth
    cutters = [
        modeling.box_between(
            f"Cutter_LED_Pocket_{square.row:02d}_{square.column:02d}",
            (
                square.led_position_mm[0] - half_x,
                square.led_position_mm[0] + half_x,
                square.led_position_mm[1] - half_y,
                square.led_position_mm[1] + half_y,
                z0,
                z1,
            ),
            construction,
        )
        for square in shared.BOARD_SQUARES
    ]
    modeling.cut_batch(plate, cutters, "Cutter_All_LED_Pockets")


def _cut_grid_grooves(
    plate: bpy.types.Object, construction: bpy.types.Collection
) -> None:
    """Engrave the nine lines each way that draw and outline the grid.

    Nine lines bound eight squares per direction, so the playing area is outlined too.
    """
    depth = shared.TILE_PLATE_GROOVE_DEPTH_MM
    half_width = shared.TILE_PLATE_GROOVE_WIDTH_MM / 2.0
    reach = shared.PLAYING_SPAN_MM / 2.0 + half_width
    z0 = TOP_Z_MM - depth
    z1 = TOP_Z_MM + shared.BOOLEAN_RECESS_OVERLAP_MM
    offsets = [
        -shared.PLAYING_SPAN_MM / 2.0 + index * shared.SQUARE_SIZE_MM
        for index in range(shared.GRID_COUNT + 1)
    ]
    # The two directions cross, so they cannot share a batch (overlapping cutters
    # in one batch break the boolean; see `modeling.cut_batch`).
    modeling.cut_batch(
        plate,
        [
            modeling.box_between(
                f"Cutter_Groove_X_{index}",
                (offset - half_width, offset + half_width, -reach, reach, z0, z1),
                construction,
            )
            for index, offset in enumerate(offsets)
        ],
        "Cutter_Grooves_Along_X",
    )
    modeling.cut_batch(
        plate,
        [
            modeling.box_between(
                f"Cutter_Groove_Y_{index}",
                (-reach, reach, offset - half_width, offset + half_width, z0, z1),
                construction,
            )
            for index, offset in enumerate(offsets)
        ],
        "Cutter_Grooves_Along_Y",
    )


def _cut_dark_squares(
    plate: bpy.types.Object, construction: bpy.types.Collection
) -> None:
    """Recess half the squares, for paint or a filament change at that height.

    Each recess is inset by half a groove width so it stops at the engraved line.
    """
    depth = shared.TILE_PLATE_DARK_SQUARE_DEPTH_MM
    half_span = (shared.SQUARE_SIZE_MM - shared.TILE_PLATE_GROOVE_WIDTH_MM) / 2.0
    z0 = TOP_Z_MM - depth
    z1 = TOP_Z_MM + shared.BOOLEAN_RECESS_OVERLAP_MM
    cutters = []
    for square in shared.BOARD_SQUARES.dark_squares:
        row, column = square.row, square.column
        x, y = square.centre_mm
        cutters.append(
            modeling.box_between(
                f"Cutter_Dark_Square_{row:02d}_{column:02d}",
                (x - half_span, x + half_span, y - half_span, y + half_span, z0, z1),
                construction,
            )
        )
    modeling.cut_batch(plate, cutters, "Cutter_All_Dark_Squares")


def _cut_screws(plate: bpy.types.Object, construction: bpy.types.Collection) -> None:
    """Through-holes with a recessed head, so nothing stands above the surface.

    Positions are the shared plate screw positions, all on the case rim.
    """
    head_depth = shared.TILE_PLATE_SCREW_HEAD_DEPTH_MM
    # The shaft and its head recess are concentric, so they go in separate
    # batches; within a batch the eight screws are far apart.
    # Through holes use the larger `BOOLEAN_THROUGH_OVERLAP_MM` so both faces are
    # fully pierced.
    modeling.cut_batch(
        plate,
        [
            modeling.cylinder_between(
                f"Cutter_Plate_Screw_{index}",
                shared.TILE_PLATE_SCREW_CLEARANCE_DIAMETER_MM,
                (x, y),
                UNDERSIDE_Z_MM - shared.BOOLEAN_THROUGH_OVERLAP_MM,
                TOP_Z_MM + shared.BOOLEAN_THROUGH_OVERLAP_MM,
                construction,
                vertices=24,
            )
            for index, (x, y) in enumerate(shared.TILE_PLATE_SCREW_POSITIONS_MM)
        ],
        "Cutter_All_Plate_Screw_Shafts",
    )
    modeling.cut_batch(
        plate,
        [
            modeling.cylinder_between(
                f"Cutter_Plate_Screw_Head_{index}",
                shared.TILE_PLATE_SCREW_HEAD_DIAMETER_MM,
                (x, y),
                TOP_Z_MM - head_depth,
                TOP_Z_MM + shared.BOOLEAN_RECESS_OVERLAP_MM,
                construction,
                vertices=24,
            )
            for index, (x, y) in enumerate(shared.TILE_PLATE_SCREW_POSITIONS_MM)
        ],
        "Cutter_All_Plate_Screw_Heads",
    )


def _cut_bezel(plate: bpy.types.Object, construction: bpy.types.Collection) -> None:
    """Button holes and the display opening over the control strip.

    Each hole sits in a shallow underside relief over its switch housing, and
    the display window sits in the recess that holds the module. A feature and
    its relief overlap, so they go in separate batches.
    """
    through = (
        UNDERSIDE_Z_MM - shared.BOOLEAN_THROUGH_OVERLAP_MM,
        TOP_Z_MM + shared.BOOLEAN_THROUGH_OVERLAP_MM,
    )
    underside = UNDERSIDE_Z_MM - shared.BOOLEAN_RECESS_OVERLAP_MM
    relief = (
        max(shared.PANEL_BUTTON_BODY_MM[:2])
        + 2.0 * shared.PANEL_BUTTON_RELIEF_CLEARANCE_MM
    ) / 2.0
    window_x, window_y = (axis / 2.0 for axis in shared.PANEL_OLED_WINDOW_MM)
    recess_x, recess_y = (axis / 2.0 for axis in shared.PANEL_OLED_RECESS_MM)
    oled_x, oled_y = shared.PANEL_OLED_CENTER_MM
    modeling.cut_batch(
        plate,
        [
            modeling.box_between(
                f"Cutter_Button_Relief_{index:02d}",
                (
                    button.x_mm - relief,
                    button.x_mm + relief,
                    button.y_mm - relief,
                    button.y_mm + relief,
                    underside,
                    UNDERSIDE_Z_MM + shared.PANEL_BUTTON_RELIEF_DEPTH_MM,
                ),
                construction,
            )
            for index, button in enumerate(shared.PANEL_BUTTONS)
        ]
        + [
            modeling.box_between(
                "Cutter_Display_Recess",
                (
                    oled_x - recess_x,
                    oled_x + recess_x,
                    oled_y - recess_y,
                    oled_y + recess_y,
                    underside,
                    UNDERSIDE_Z_MM + shared.PANEL_OLED_RECESS_DEPTH_MM,
                ),
                construction,
            )
        ],
        "Cutter_All_Bezel_Reliefs",
    )
    modeling.cut_batch(
        plate,
        [
            modeling.cylinder_between(
                f"Cutter_Button_{index:02d}",
                shared.PANEL_BUTTON_HOLE_DIAMETER_MM,
                button.position_mm,
                *through,
                construction,
                vertices=32,
            )
            for index, button in enumerate(shared.PANEL_BUTTONS)
        ]
        + [
            modeling.box_between(
                "Cutter_Display_Window",
                (
                    oled_x - window_x,
                    oled_x + window_x,
                    oled_y - window_y,
                    oled_y + window_y,
                    *through,
                ),
                construction,
            )
        ],
        "Cutter_All_Bezel_Openings",
    )


def build(output_directory: Path = GENERATED) -> None:
    """Generate `tile-plate.blend` and `tile-plate.png` into `output_directory`."""
    workspace = project.setup_printable(
        "Printable Tile Plate",
        shared.BLENDER_SCALE_LENGTH,
    )
    project.apply_metadata(
        workspace.scene,
        TilePlateMetadata(
            design_status="Printable prototype",
            project_role="Single overlay replacing 128 tile prints",
            grid_rows=shared.GRID_COUNT,
            grid_columns=shared.GRID_COUNT,
            square_count=shared.GRID_COUNT * shared.GRID_COUNT,
            dark_square_count=len(shared.BOARD_SQUARES.dark_squares),
            diffuser_skin_mm=shared.TILE_PLATE_DIFFUSER_SKIN_MM,
            panel_button_count=shared.PANEL_BUTTON_COUNT,
            # Recorded for reviewers: the plate exceeds a desktop printer bed, so it is
            # quoted from a print service (see the CAD README).
            reference_build_volume_mm="420 x 420 x 420 print service",
        ),
    )

    plate_material = materials.solid(
        "Ivory printable plate", (0.62, 0.58, 0.50, 1.0), 0.44
    )
    floor_material = materials.solid("Studio floor", (0.025, 0.028, 0.03, 1.0), 0.48)

    plate = add_plate(workspace.printable, workspace.construction, plate_material)
    # Cutter helpers must not appear in the render.
    workspace.construction.hide_render = True
    workspace.construction.hide_viewport = True
    presentation.add_studio(
        workspace.studio,
        floor_material,
        (1500.0, 1500.0),
        # Camera position and look-at point: aim at the plate's top face.
        (300.0, -360.0, 320.0),
        (0.0, 0.0, shared.CASE_HEIGHT_MM),
        56,
        presentation.BOARD_STUDIO_LIGHTS,
    )

    output_path = project.save_printable(
        plate,
        shared.REFERENCE_SERVICE_BUILD_VOLUME_MM,
        output_directory,
        NAME,
        "plate_volume_mm3",
    )
    print(f"Saved {output_path}")


if __name__ == "__main__":
    build(project.output_directory(GENERATED))
