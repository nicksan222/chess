"""The concrete printable board-case; all dimensions belong to the shared contract."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cad.harness.base.component import PrintableComponent
from shared import dimensions as shared

if TYPE_CHECKING:
    import bpy

FLOOR_VENT_COUNT = 5
FLOOR_VENT_PITCH_MM = 8.0


class BoardCase(PrintableComponent):
    output_name = "board-case"
    scene_name = "Printable Board Case"
    camera_location = (330.0, -420.0, 320.0)
    camera_target = (0.0, shared.CASE_CENTER_OFFSET_Y_MM, 6.0)
    volume_property = "case_volume_mm3"

    def __init__(self) -> None:
        super().__init__("Printable_Board_Case")

    def build(
        self,
        collection: bpy.types.Collection,
        construction: bpy.types.Collection,
        palette: dict[str, bpy.types.Material],
    ) -> tuple[bpy.types.Object, ...]:
        from cad.harness.base.blender import materials

        material = materials.solid(
            "Graphite printable case", (0.035, 0.045, 0.05, 1.0), 0.32
        )
        part = add_case(collection, construction, material)
        return (part,)


def add_case(
    printable: bpy.types.Collection,
    construction: bpy.types.Collection,
    case_material: bpy.types.Material,
) -> bpy.types.Object:
    """Build the case: a solid block, then each feature applied in order.

    Order is functional: the cavity must be cut before the bosses are added (bosses
    are a union, so hollowing afterwards would remove them), and the pilots are cut last,
    into the bosses and the rim. The smaller wall and floor features go in between.
    """
    from cad.harness.base.blender import modeling

    case = modeling.rounded_box(
        "Printable_Board_Case",
        shared.CASE_OUTER_SIZE_MM,
        (0.0, shared.CASE_CENTER_OFFSET_Y_MM, shared.CASE_HEIGHT_MM / 2.0),
        shared.CASE_OUTER_RADIUS_MM,
        printable,
    )
    case.data.materials.append(case_material)
    case["purpose"] = "Open tub for one PCB; the plate carries the bezel"

    _hollow_cavity(case, construction)
    _cut_plate_rebate(case, construction)
    _cut_rear_apertures(case, construction)
    _cut_side_slot(case, construction)
    _cut_floor_vents(case, construction)
    _add_support_bosses(case, construction)
    _cut_plate_screws(case, construction)
    return case


def _hollow_cavity(case: bpy.types.Object, construction: bpy.types.Collection) -> None:
    """Remove the interior: a cavity under the board and a pocket around it.

    The cavity is narrower than the board by the ledge overlap, so the wall
    left between the two carries the board edge. The pocket is the board
    outline plus clearance and runs up to the rim the plate rests on.
    """
    import bpy

    from cad.harness.base.blender import modeling

    # The rim the plate rests on is one plate thickness below the top of the case.
    rim_z = shared.CASE_HEIGHT_MM - shared.TILE_PLATE_THICKNESS_MM
    # The cavity overshoots into the pocket so the two never share a face.
    cavity_top = shared.PCB_UNDERSIDE_Z_MM + shared.PCB_THICKNESS_MM / 2.0
    pocket_top = rim_z + shared.BOOLEAN_THROUGH_OVERLAP_MM
    for name, size, bottom, top, radius in (
        (
            "Cutter_Case_Cavity",
            shared.CASE_CAVITY_SIZE_MM,
            shared.CASE_FLOOR_MM,
            cavity_top,
            1.0,
        ),
        (
            "Cutter_PCB_Pocket",
            shared.PCB_POCKET_SIZE_MM,
            shared.PCB_UNDERSIDE_Z_MM,
            pocket_top,
            shared.PCB_POCKET_RADIUS_MM,
        ),
    ):
        cutter = modeling.rounded_box(
            name,
            (size[0], size[1], top - bottom),
            (0.0, shared.CASE_CENTER_OFFSET_Y_MM, (bottom + top) / 2.0),
            radius,
            construction,
        )
        modeling.boolean_apply(case, cutter, "DIFFERENCE")
        bpy.data.objects.remove(cutter, do_unlink=True)


def _cut_plate_rebate(
    case: bpy.types.Object, construction: bpy.types.Collection
) -> None:
    """Open the top over the whole board so the plate sits flush on the rim."""
    import bpy

    from cad.harness.base.blender import modeling

    depth = shared.TILE_PLATE_REBATE_DEPTH_MM + shared.BOOLEAN_THROUGH_OVERLAP_MM
    rebate = modeling.rounded_box(
        "Cutter_Plate_Rebate",
        (*shared.CASE_PLATE_REBATE_MM, depth),
        (
            0.0,
            shared.CASE_CENTER_OFFSET_Y_MM,
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


def _cut_rear_apertures(
    case: bpy.types.Object, construction: bpy.types.Collection
) -> None:
    """Panel-mounted power input on the back wall, wired to the board.

    The snap-in rocker and the nut-held jack each need a thin panel, so the
    wall is pocketed from the inside down to each part's panel thickness.
    """
    from cad.harness.base.blender import modeling

    wall_y = shared.CASE_CENTER_OFFSET_Y_MM + shared.CASE_DEPTH_MM / 2.0
    depth = 2.0 * shared.CASE_FRAME_WIDTH_MM
    center_y = wall_y - depth / 2.0 + shared.BOOLEAN_THROUGH_OVERLAP_MM
    z = shared.CASE_REAR_APERTURE_CENTER_Z_MM

    jack = modeling.cylinder(
        "Cutter_Jack_Aperture",
        shared.CASE_JACK_APERTURE_DIAMETER_MM,
        depth,
        (shared.CASE_JACK_APERTURE_CENTER_X_MM, center_y, z),
        construction,
        vertices=48,
    )
    # Rotate the cylinder 90 degrees so its axis points through the rear wall (Y).
    jack.rotation_euler = (1.5707963267948966, 0.0, 0.0)
    rocker = modeling.rounded_box(
        "Cutter_Rocker_Aperture",
        (shared.CASE_ROCKER_APERTURE_MM[0], depth, shared.CASE_ROCKER_APERTURE_MM[1]),
        (shared.CASE_ROCKER_APERTURE_CENTER_X_MM, center_y, z),
        0.6,
        construction,
    )
    # Round jack hole and rectangular rocker cutout through the wall (disjoint cutters).
    modeling.cut_batch(case, [jack, rocker], "Cutter_All_Rear_Apertures")

    # Inner pockets thin the wall to each part's panel thickness; they start inside the
    # cavity so they open into it, and stop below the roof that keeps the PCB ledge whole.
    cavity_y = shared.CASE_CENTER_OFFSET_Y_MM + shared.CASE_CAVITY_SIZE_MM[1] / 2.0
    bottom, top = shared.CASE_WALL_POCKET_Z_MM
    pockets = [
        modeling.box_between(
            f"Cutter_{name}_Wall_Pocket",
            (
                centre_x - width / 2.0,
                centre_x + width / 2.0,
                cavity_y - shared.BOOLEAN_THROUGH_OVERLAP_MM,
                wall_y - panel,
                # Dips just under the floor surface so no face is coplanar with it.
                bottom - shared.BOOLEAN_RECESS_OVERLAP_MM,
                top,
            ),
            construction,
        )
        for name, centre_x, width, panel in (
            (
                "Rocker",
                shared.CASE_ROCKER_APERTURE_CENTER_X_MM,
                shared.CASE_ROCKER_POCKET_WIDTH_MM,
                shared.CASE_ROCKER_PANEL_THICKNESS_MM,
            ),
            (
                "Jack",
                shared.CASE_JACK_APERTURE_CENTER_X_MM,
                shared.CASE_JACK_POCKET_WIDTH_MM,
                shared.CASE_JACK_PANEL_THICKNESS_MM,
            ),
        )
    ]
    modeling.cut_batch(case, pockets, "Cutter_All_Rear_Wall_Pockets")


def _cut_side_slot(case: bpy.types.Object, construction: bpy.types.Collection) -> None:
    """A slot in the right wall, level with the Pi's microSD socket.

    The wall is pocketed from inside around it so a card standing proud of the
    Pi edge clears the wall and its edge can be reached with tweezers.
    """
    from cad.harness.base.blender import modeling

    wall_x = shared.CASE_WIDTH_MM / 2.0
    depth = 2.0 * shared.CASE_FRAME_WIDTH_MM
    slot_y = shared.CASE_SD_SLOT_CENTER_Y_MM
    slot = modeling.rounded_box(
        "Cutter_Card_Slot",
        (depth, shared.CASE_SD_SLOT_MM[0], shared.CASE_SD_SLOT_MM[1]),
        (
            wall_x - depth / 2.0 + shared.BOOLEAN_THROUGH_OVERLAP_MM,
            slot_y,
            shared.CASE_SD_SLOT_CENTER_Z_MM,
        ),
        0.6,
        construction,
    )
    modeling.cut_batch(case, [slot], "Cutter_Card_Slot_Combined")
    cavity_x = shared.CASE_CAVITY_SIZE_MM[0] / 2.0
    bottom, top = shared.CASE_WALL_POCKET_Z_MM
    half_width = shared.CASE_SD_POCKET_WIDTH_MM / 2.0
    pocket = modeling.box_between(
        "Cutter_Card_Wall_Pocket",
        (
            cavity_x - shared.BOOLEAN_THROUGH_OVERLAP_MM,
            wall_x - shared.CASE_SD_PANEL_THICKNESS_MM,
            slot_y - half_width,
            slot_y + half_width,
            bottom - shared.BOOLEAN_RECESS_OVERLAP_MM,
            top,
        ),
        construction,
    )
    modeling.cut_batch(case, [pocket], "Cutter_Card_Wall_Pocket_Batch")


def _cut_floor_vents(
    case: bpy.types.Object, construction: bpy.types.Collection
) -> None:
    """Slots under the Pi, along its long axis, so it is not sealed in."""
    from cad.harness.base.blender import modeling

    height = shared.CASE_FLOOR_MM + 2.0 * shared.BOOLEAN_THROUGH_OVERLAP_MM
    first = -(FLOOR_VENT_COUNT - 1) / 2.0 * FLOOR_VENT_PITCH_MM
    pi_x, pi_y = shared.PI_CENTER_MM
    cutters = [
        modeling.rounded_box(
            f"Cutter_Floor_Vent_{index}",
            (shared.CASE_VENT_SLOT_MM[0], shared.CASE_VENT_SLOT_MM[1], height),
            (
                pi_x,
                pi_y + first + index * FLOOR_VENT_PITCH_MM,
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
    from cad.harness.base.blender import modeling

    bosses = [
        modeling.cylinder_between(
            f"Boss_PCB_Support_{index:02d}",
            shared.PCB_SUPPORT_BOSS_DIAMETER_MM,
            (x, y),
            shared.CASE_FLOOR_MM,
            shared.PCB_UNDERSIDE_Z_MM,
            construction,
            vertices=32,
        )
        for index, (x, y) in enumerate(shared.PCB_SUPPORT_POSITIONS_MM)
    ]
    modeling.union_batch(case, bosses, "Boss_All_PCB_Supports")

    pilot_depth = shared.PCB_SUPPORT_PILOT_DEPTH_MM
    pilots = [
        modeling.cylinder_between(
            f"Cutter_Support_Pilot_{index:02d}",
            shared.PCB_SUPPORT_PILOT_DIAMETER_MM,
            (x, y),
            shared.PCB_UNDERSIDE_Z_MM - pilot_depth,
            shared.PCB_UNDERSIDE_Z_MM + shared.BOOLEAN_RECESS_OVERLAP_MM,
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
    from cad.harness.base.blender import modeling

    depth = shared.PCB_SUPPORT_PILOT_DEPTH_MM
    ledge_top = shared.CASE_HEIGHT_MM - shared.TILE_PLATE_THICKNESS_MM
    pilots = [
        modeling.cylinder_between(
            f"Cutter_Plate_Screw_{index}",
            shared.PCB_SUPPORT_PILOT_DIAMETER_MM,
            (x, y),
            ledge_top - depth,
            ledge_top + shared.BOOLEAN_RECESS_OVERLAP_MM,
            construction,
            vertices=24,
        )
        for index, (x, y) in enumerate(shared.TILE_PLATE_SCREW_POSITIONS_MM)
    ]
    modeling.cut_batch(case, pilots, "Cutter_All_Plate_Screw_Pilots")
