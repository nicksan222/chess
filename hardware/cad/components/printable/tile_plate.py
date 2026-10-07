"""The concrete printable tile-plate; all dimensions belong to the shared contract."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cad.harness.base.component import PrintableComponent
from shared import dimensions as shared

if TYPE_CHECKING:
    import bpy

TOP_Z_MM = shared.CASE_HEIGHT_MM
UNDERSIDE_Z_MM = shared.CASE_HEIGHT_MM - shared.TILE_PLATE_THICKNESS_MM


class TilePlate(PrintableComponent):
    output_name = "tile-plate"
    scene_name = "Printable Tile Plate"
    camera_location = (300.0, -360.0, 320.0)
    camera_target = (0.0, 0.0, shared.CASE_HEIGHT_MM)
    volume_property = "plate_volume_mm3"

    def __init__(self) -> None:
        super().__init__("Printable_Tile_Plate")

    def build(
        self,
        collection: bpy.types.Collection,
        construction: bpy.types.Collection,
        palette: dict[str, bpy.types.Material],
    ) -> tuple[bpy.types.Object, ...]:
        from cad.harness.base.blender import materials

        material = materials.solid("Light squares", (0.72, 0.66, 0.53, 1.0), 0.44)
        part = add_plate(collection, construction, material)
        _color_squares(part)
        return (part,)


def add_plate(
    printable: bpy.types.Collection,
    construction: bpy.types.Collection,
    plate_material: bpy.types.Material,
) -> bpy.types.Object:
    """Build the plate: a slab, then each feature cut in turn.

    The slab is centred on the plate's own offset (the plate covers the control strip
    too, so it is not centred on the playing area) and bevelled 0.8 mm.
    """
    from cad.harness.base.blender import modeling

    plate = modeling.rounded_box(
        "Printable_Tile_Plate",
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
    _reinforce_piece_seats(plate, construction)
    _cut_led_pockets(plate, construction)
    _cut_led_windows(plate, construction)
    _cut_grid_grooves(plate, construction)
    _cut_dark_squares(plate, construction)
    _cut_piece_seats(plate, construction)
    _cut_screws(plate, construction)
    _cut_control_surface(plate, construction)
    _cut_bezel(plate, construction)
    _add_display_bezel(plate, construction)
    _engrave_control_labels(plate, construction)
    return plate


def _cut_underside_pockets(
    plate: bpy.types.Object, construction: bpy.types.Collection
) -> None:
    """One pocket per square: removes weight and clears the Hall sensors.

    Pockets sit on the square grid and leave ribs on the grid lines. They overshoot
    the underside by `BOOLEAN_RECESS_OVERLAP_MM` so the cutter face is not coplanar
    with the plate face (coplanar faces defeat the exact solver).
    """
    from cad.harness.base.blender import modeling

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


def _reinforce_piece_seats(
    plate: bpy.types.Object, construction: bpy.types.Collection
) -> None:
    """Solid square supports keep the locating holes from thinning sensor covers."""
    from cad.harness.base.blender import modeling

    half = shared.TILE_PLATE_PIECE_SEAT_SUPPORT_SIDE_MM / 2
    modeling.union_batch(
        plate,
        [
            modeling.box_between(
                f"Seat_Support_{square.name}",
                (
                    square.centre_mm[0] - half,
                    square.centre_mm[0] + half,
                    square.centre_mm[1] - half,
                    square.centre_mm[1] + half,
                    UNDERSIDE_Z_MM,
                    UNDERSIDE_Z_MM
                    + shared.TILE_PLATE_UNDERSIDE_POCKET_DEPTH_MM
                    + shared.BOOLEAN_RECESS_OVERLAP_MM,
                ),
                construction,
            )
            for square in shared.BOARD_SQUARES
        ],
        "All_Piece_Seat_Supports",
    )


def _cut_piece_seats(
    plate: bpy.types.Object, construction: bpy.types.Collection
) -> None:
    """A square ring channel around a retained island, accepting a square ring foot."""
    from cad.harness.base.blender import modeling

    half = shared.TILE_PLATE_PIECE_SEAT_SIDE_MM / 2
    inner_half = shared.TILE_PLATE_PIECE_SEAT_INNER_SIDE_MM / 2
    cutters = []
    for square in shared.BOARD_SQUARES:
        x, y = square.centre_mm
        surface = TOP_Z_MM - (
            shared.TILE_PLATE_DARK_SQUARE_DEPTH_MM if square.is_dark else 0
        )
        floor = surface - shared.TILE_PLATE_PIECE_SEAT_DEPTH_MM
        ring = modeling.box_between(
            f"Cutter_Piece_Ring_{square.name}",
            (
                x - half,
                x + half,
                y - half,
                y + half,
                floor,
                TOP_Z_MM + shared.BOOLEAN_RECESS_OVERLAP_MM,
            ),
            construction,
        )
        island = modeling.box_between(
            f"Preserved_Piece_Island_{square.name}",
            (
                x - inner_half,
                x + inner_half,
                y - inner_half,
                y + inner_half,
                floor - shared.BOOLEAN_RECESS_OVERLAP_MM,
                TOP_Z_MM + 2 * shared.BOOLEAN_RECESS_OVERLAP_MM,
            ),
            construction,
        )
        modeling.cut_batch(ring, [island], f"Cutter_Ring_Without_Island_{square.name}")
        cutters.append(ring)
    modeling.cut_batch(plate, cutters, "Cutter_All_Piece_Rings")


def _cut_led_pockets(
    plate: bpy.types.Object, construction: bpy.types.Collection
) -> None:
    """Package clearance over each LED, with a roof around its through-window.

    The pocket is centred on the LED position (not the square centre) from the shared
    LED offset; a separate through-cut exposes the emitter from outside.
    """
    from cad.harness.base.blender import modeling

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


def _cut_led_windows(
    plate: bpy.types.Object, construction: bpy.types.Collection
) -> None:
    """Expose each real emitter through the plate, including the pocket roof."""
    from cad.harness.base.blender import modeling

    half_x, half_y = (side / 2 for side in shared.TILE_PLATE_LED_WINDOW_MM)
    modeling.cut_batch(
        plate,
        [
            modeling.box_between(
                f"Cutter_LED_Window_{square.name}",
                (
                    square.led_position_mm[0] - half_x,
                    square.led_position_mm[0] + half_x,
                    square.led_position_mm[1] - half_y,
                    square.led_position_mm[1] + half_y,
                    UNDERSIDE_Z_MM - shared.BOOLEAN_THROUGH_OVERLAP_MM,
                    TOP_Z_MM + shared.BOOLEAN_THROUGH_OVERLAP_MM,
                ),
                construction,
            )
            for square in shared.BOARD_SQUARES
        ],
        "Cutter_All_LED_Windows",
    )


def _cut_grid_grooves(
    plate: bpy.types.Object, construction: bpy.types.Collection
) -> None:
    """Engrave the nine lines each way that draw and outline the grid.

    Nine lines bound eight squares per direction, so the playing area is outlined too.
    """
    from cad.harness.base.blender import modeling

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
    from cad.harness.base.blender import modeling

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
    from cad.harness.base.blender import modeling

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


def _cut_control_surface(
    plate: bpy.types.Object, construction: bpy.types.Collection
) -> None:
    """One continuous recessed strip for buttons and display, with no raised island."""
    from cad.harness.base.blender import modeling

    half_x, half_y = (side / 2 for side in shared.PANEL_SURFACE_SIZE_MM)
    recess = modeling.box_between(
        "Cutter_Control_Surface",
        (
            -half_x,
            half_x,
            shared.PANEL_ORIGIN_Y_MM - half_y,
            shared.PANEL_ORIGIN_Y_MM + half_y,
            TOP_Z_MM - shared.PANEL_SURFACE_RECESS_MM,
            TOP_Z_MM + shared.BOOLEAN_RECESS_OVERLAP_MM,
        ),
        construction,
    )
    modeling.cut_batch(plate, [recess], "Cutter_All_Control_Surface")


def _cut_bezel(plate: bpy.types.Object, construction: bpy.types.Collection) -> None:
    """Button holes and the display opening over the control strip.

    Each hole sits in a shallow underside relief over its switch housing, and
    the display window sits in the recess that holds the module. A feature and
    its relief overlap, so they go in separate batches.
    """
    from cad.harness.base.blender import modeling

    through = (
        UNDERSIDE_Z_MM - shared.BOOLEAN_THROUGH_OVERLAP_MM,
        TOP_Z_MM + shared.BOOLEAN_THROUGH_OVERLAP_MM,
    )
    underside = UNDERSIDE_Z_MM - shared.BOOLEAN_RECESS_OVERLAP_MM
    relief = (
        max(shared.PANEL_BUTTON_BODY_MM[:2])
        + 2.0 * shared.PANEL_BUTTON_RELIEF_CLEARANCE_MM
    ) / 2.0
    window_x, window_y = (axis / 2.0 for axis in shared.PANEL_OLED_WIRE_OPENING_MM)
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
                "Cutter_Display_Wire_Opening",
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


def _add_display_bezel(
    plate: bpy.types.Object, construction: bpy.types.Collection
) -> None:
    """A concealed-carrier bezel with a full viewing window and mounting ears."""
    from cad.harness.base.blender import modeling

    x, y = shared.PANEL_OLED_CENTER_MM
    outer_x, outer_y = (v / 2 for v in shared.PANEL_OLED_BEZEL_OUTER_MM)
    inner_x, inner_y = (v / 2 for v in shared.PANEL_OLED_BEZEL_INNER_MM)
    top = shared.PANEL_OLED_BEZEL_TOP_Z_MM
    bezel = modeling.box_between(
        "Display_Bezel",
        (
            x - outer_x,
            x + outer_x,
            y - outer_y,
            y + outer_y,
            TOP_Z_MM - shared.PANEL_SURFACE_RECESS_MM - 0.2,
            top,
        ),
        construction,
    )
    modeling.union_batch(plate, [bezel], "Owning display bezel")
    # Module cavity clears the PCB and iron frame below a 1 mm bezel roof.
    cavity = modeling.box_between(
        "Display_Module_Cavity",
        (
            x - inner_x,
            x + inner_x,
            y - inner_y,
            y + inner_y,
            UNDERSIDE_Z_MM - 0.4,
            shared.PANEL_OLED_SCREEN_Z_MM + 0.1,
        ),
        construction,
    )
    modeling.cut_batch(plate, [cavity], "Display module cavity")
    screen_x = x + shared.PANEL_OLED_SCREEN_OFFSET_MM[0]
    screen_y = y + shared.PANEL_OLED_SCREEN_OFFSET_MM[1]
    hx, hy = (v / 2 + 0.5 for v in shared.PANEL_OLED_SCREEN_SIZE_MM)
    window = modeling.box_between(
        "Display_Viewing_Window",
        (
            screen_x - hx,
            screen_x + hx,
            screen_y - hy,
            screen_y + hy,
            UNDERSIDE_Z_MM - 0.4,
            top + 0.4,
        ),
        construction,
    )
    modeling.cut_batch(plate, [window], "Full OLED viewing window")
    # Four supplier mounting holes sit on printed ledges beneath the carrier.
    # Each ledge joins the outer wall, leaving the screen and SMD region clear.
    bottom = shared.PANEL_OLED_LEDGE_BOTTOM_Z_MM
    half_ledge = shared.PANEL_OLED_LEDGE_WIDTH_MM / 2
    additions = []
    pilots = []
    for i, (dx, dy) in enumerate(shared.PANEL_OLED_MOUNT_HOLES_MM):
        cx, cy = x + dx, y + dy
        sign = 1 if dx > 0 else -1
        outer_edge = x + sign * (outer_x + shared.PANEL_OLED_LEDGE_WALL_REACH_MM)
        outside_module = x + sign * (inner_x - shared.BOOLEAN_RECESS_OVERLAP_MM)
        additions.append(
            modeling.box_between(
                f"Display_ledge_{i}",
                (
                    min(cx - half_ledge, outer_edge),
                    max(cx + half_ledge, outer_edge),
                    cy - half_ledge,
                    cy + half_ledge,
                    bottom,
                    shared.PANEL_OLED_PCB_BOTTOM_Z_MM,
                ),
                construction,
            )
        )
        additions.append(
            modeling.box_between(
                f"Display_ledge_root_{i}",
                (
                    min(
                        outside_module,
                        outer_edge - sign * shared.BOOLEAN_RECESS_OVERLAP_MM,
                    ),
                    max(
                        outside_module,
                        outer_edge - sign * shared.BOOLEAN_RECESS_OVERLAP_MM,
                    ),
                    cy - half_ledge + shared.BOOLEAN_RECESS_OVERLAP_MM,
                    cy + half_ledge - shared.BOOLEAN_RECESS_OVERLAP_MM,
                    bottom + shared.BOOLEAN_RECESS_OVERLAP_MM,
                    TOP_Z_MM - shared.PANEL_SURFACE_RECESS_MM + 0.1,
                ),
                construction,
            )
        )
        pilots.append(
            modeling.cylinder_between(
                f"Display_pilot_{i}",
                shared.PANEL_OLED_PILOT_DIAMETER_MM,
                (cx, cy),
                bottom + shared.PANEL_OLED_PILOT_FLOOR_MM,
                shared.PANEL_OLED_PCB_BOTTOM_Z_MM + 0.2,
                construction,
                vertices=24,
            )
        )
    # Roots overlap their arms on every axis, avoiding coplanar boolean seams.
    # Join each bracket before attaching it to the detailed plate mesh.
    for arm, root in zip(additions[::2], additions[1::2]):
        modeling.union_batch(arm, [root], "Display bracket root")
        modeling.union_batch(plate, [arm], "Display mounting ledge")
    modeling.cut_batch(plate, pilots, "Display mounting pilots")
    modeling.cut_batch(
        plate,
        [
            modeling.cylinder_between(
                f"Display_screw_access_{i}",
                shared.PANEL_OLED_FASTENER_ACCESS_DIAMETER_MM,
                (x + dx, y + dy),
                shared.PANEL_OLED_PCB_BOTTOM_Z_MM
                + shared.PANEL_OLED_PCB_THICKNESS_MM
                - shared.BOOLEAN_RECESS_OVERLAP_MM,
                top + shared.BOOLEAN_THROUGH_OVERLAP_MM,
                construction,
                vertices=32,
            )
            for i, (dx, dy) in enumerate(shared.PANEL_OLED_MOUNT_HOLES_MM)
        ],
        "Display screw access",
    )


def _engrave_control_labels(
    plate: bpy.types.Object, construction: bpy.types.Collection
) -> None:
    """Subtract the letters from the owning mesh; these are real printable recesses."""
    import bpy

    from cad.harness.base.blender import modeling

    surface = TOP_Z_MM - shared.PANEL_SURFACE_RECESS_MM
    font = bpy.data.fonts.load("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    font.pack()
    cutters = []
    for button in shared.PANEL_BUTTONS:
        bpy.ops.object.text_add(
            location=(
                *button.legend_position_mm,
                surface
                + (shared.BOOLEAN_RECESS_OVERLAP_MM - shared.PANEL_LEGEND_DEPTH_MM) / 2,
            )
        )
        label = modeling.active_object("engraving button legend")
        text = modeling.require_object_data(label, bpy.types.TextCurve)
        text.body, text.align_x = button.name, "CENTER"
        text.font = font
        text.size = shared.PANEL_LEGEND_SIZE_MM
        text.extrude = (
            shared.PANEL_LEGEND_DEPTH_MM + shared.BOOLEAN_RECESS_OVERLAP_MM
        ) / 2
        label.name = f"Cutter_Legend_{button.switch_reference}"
        bpy.ops.object.convert(target="MESH")
        # Font conversion separates face and wall vertices. Join their exact
        # coincident seams so the engraving operand is a closed solid.
        from cad.harness.base.blender.validation import weld_solid

        weld_solid(label)
        triangulate = label.modifiers.new(
            name="Closed letter faces", type="TRIANGULATE"
        )
        bpy.ops.object.modifier_apply(modifier=triangulate.name)
        modeling.move_to_collection(label, construction)
        cutters.append(label)
    # The manifold solver preserves collinear letter edges that the exact
    # solver leaves as open T-junctions on the recess floor.
    modeling.cut_batch(plate, cutters, "Engraved control legends", solver="MANIFOLD")


def _color_squares(plate: bpy.types.Object) -> None:
    """Color the actual square faces and channels using the shared square layout."""
    import bpy

    from cad.harness.base.blender import materials, modeling

    dark = materials.solid("Dark squares", (0.035, 0.045, 0.05, 1.0), 0.42)
    dark_index = len(plate.data.materials)
    plate.data.materials.append(dark)
    bpy.context.view_layer.update()
    mesh = modeling.require_object_data(plate, bpy.types.Mesh)
    half_square = shared.SQUARE_SIZE_MM / 2
    half_board = shared.PLAYING_SPAN_MM / 2
    for face in mesh.polygons:
        face.material_index = 0
        # The large perimeter face can have its centroid inside the board, despite
        # all its material being outside it. Keep perimeter/bezel faces light.
        vertices = [
            plate.matrix_world @ mesh.vertices[index].co for index in face.vertices
        ]
        if any(
            abs(point.x) > half_board or abs(point.y) > half_board for point in vertices
        ):
            continue
        center = plate.matrix_world @ face.center
        for square in shared.BOARD_SQUARES:
            if (
                abs(center.x - square.centre_mm[0]) < half_square
                and abs(center.y - square.centre_mm[1]) < half_square
            ):
                face.material_index = dark_index if square.is_dark else 0
                break
