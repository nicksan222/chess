"""Compose generated board, lid, and tray sources into assembly views."""

from pathlib import Path
import sys

import bpy
from mathutils import Vector


PROJECT_DIR = Path(__file__).parent
BLENDER_ROOT = PROJECT_DIR.parent
sys.path.insert(0, str(BLENDER_ROOT))

import dimensions as shared  # noqa: E402
import materials  # noqa: E402
import modeling  # noqa: E402


OUTPUT_PATH = PROJECT_DIR / "board-assembly.blend"
RENDER_DIR = PROJECT_DIR / "renders"
BOARD_PROJECT_PATH = PROJECT_DIR.parent / "board-skeleton" / "board-skeleton.blend"
TILE_TOP_PATH = PROJECT_DIR.parent / "single-tile" / "top" / "tile-top.blend"
TILE_BOTTOM_PATH = (
    PROJECT_DIR.parent / "single-tile" / "bottom" / "tile-bottom.blend"
)


def load_tile_parts() -> dict[str, bpy.types.Object]:
    parts = {}
    parts.update(modeling.load_objects(TILE_TOP_PATH, ("Tile_Top_Lid",)))
    parts.update(modeling.load_objects(TILE_BOTTOM_PATH, ("Tile_Bottom_Tray",)))
    for source in parts.values():
        if abs(source.dimensions.x - shared.TILE_SIZE_MM) > 0.01:
            raise RuntimeError(
                f"Tile source does not match shared dimensions: {source.name}"
            )
    return parts


def add_tile(
    collection: bpy.types.Collection,
    source_parts: dict[str, bpy.types.Object],
    top_material: bpy.types.Material,
    bottom_material: bpy.types.Material,
    prefix: str,
    row: int,
    column: int,
    x: float,
    y: float,
    z_offset: float = 0.0,
) -> None:
    for part_name, source in source_parts.items():
        instance = source.copy()
        instance.name = f"{prefix}_{row:02d}_{column:02d}_{part_name}"
        collection.objects.link(instance)
        instance.location = source.location + Vector(
            (x, y, shared.BOARD_FLOOR_THICKNESS_MM + z_offset)
        )
        if instance.material_slots:
            slot = instance.material_slots[0]
            slot.link = "OBJECT"
            slot.material = (
                top_material if part_name == "Tile_Top_Lid" else bottom_material
            )
        instance["board_row"] = row
        instance["board_column"] = column
        instance["mounting_method"] = "Velcro; optional aligned screws"


def add_loading_view(
    loading: bpy.types.Collection,
    source_parts: dict[str, bpy.types.Object],
    maple: bpy.types.Material,
    walnut: bpy.types.Material,
    polymer: bpy.types.Material,
) -> None:
    grid_half = shared.PLAYING_SPAN_MM / 2.0
    for row in range(3):
        y = grid_half - (row + 0.5) * shared.SQUARE_SIZE_MM
        for column in range(shared.GRID_COUNT):
            x = -grid_half + (column + 0.5) * shared.SQUARE_SIZE_MM
            add_tile(
                loading,
                source_parts,
                maple if (row + column) % 2 == 0 else walnut,
                polymer,
                "Installed_Tile",
                row,
                column,
                x,
                y,
            )

    row, column = 5, 4
    add_tile(
        loading,
        source_parts,
        maple if (row + column) % 2 == 0 else walnut,
        polymer,
        "Placement_Tile",
        row,
        column,
        -grid_half + (column + 0.5) * shared.SQUARE_SIZE_MM,
        grid_half - (row + 0.5) * shared.SQUARE_SIZE_MM,
        z_offset=22.0,
    )


def add_finished_view(
    finished: bpy.types.Collection,
    source_parts: dict[str, bpy.types.Object],
    maple: bpy.types.Material,
    walnut: bpy.types.Material,
    polymer: bpy.types.Material,
) -> None:
    grid_half = shared.PLAYING_SPAN_MM / 2.0
    for row in range(shared.GRID_COUNT):
        y = grid_half - (row + 0.5) * shared.SQUARE_SIZE_MM
        for column in range(shared.GRID_COUNT):
            x = -grid_half + (column + 0.5) * shared.SQUARE_SIZE_MM
            add_tile(
                finished,
                source_parts,
                maple if (row + column) % 2 == 0 else walnut,
                polymer,
                "Finished_Tile",
                row,
                column,
                x,
                y,
            )


def render_views(
    loading: bpy.types.Collection,
    finished: bpy.types.Collection,
) -> None:
    RENDER_DIR.mkdir(parents=True, exist_ok=True)
    scene = bpy.context.scene
    camera = bpy.data.objects["Camera_Render"]

    loading.hide_render = False
    finished.hide_render = True
    camera.location = (330.0, -430.0, 310.0)
    camera.data.lens = 56
    modeling.point_at(camera, Vector((0.0, -15.0, 8.0)))
    scene.render.filepath = str(RENDER_DIR / "loading.png")
    bpy.ops.render.render(write_still=True)

    loading.hide_render = True
    finished.hide_render = False
    camera.location = (310.0, -370.0, 300.0)
    camera.data.lens = 58
    modeling.point_at(camera, Vector((0.0, 0.0, 6.0)))
    scene.render.filepath = str(RENDER_DIR / "finished.png")
    bpy.ops.render.render(write_still=True)
    finished.hide_render = True


def build() -> None:
    for source_path in (BOARD_PROJECT_PATH, TILE_TOP_PATH, TILE_BOTTOM_PATH):
        if not source_path.is_file():
            raise RuntimeError(f"Generate element project first: {source_path}")

    bpy.ops.wm.open_mainfile(filepath=str(BOARD_PROJECT_PATH))
    bpy.context.preferences.filepaths.save_version = 0
    scene = bpy.context.scene
    scene.name = "Printable Board Tile Assembly"
    scene["project_role"] = "Composite presentation only"
    scene["board_source"] = str(BOARD_PROJECT_PATH.relative_to(BLENDER_ROOT))
    scene["tile_top_source"] = str(TILE_TOP_PATH.relative_to(BLENDER_ROOT))
    scene["tile_bottom_source"] = str(TILE_BOTTOM_PATH.relative_to(BLENDER_ROOT))
    scene["printable_geometry_redefined"] = False
    scene["finished_tile_count"] = shared.GRID_COUNT * shared.GRID_COUNT

    loading = modeling.new_collection("LOADING_TILE_REFERENCES")
    finished = modeling.new_collection("FINISHED_TILE_REFERENCES")
    source_parts = load_tile_parts()
    maple = materials.wood(
        "Maple assembly tiles",
        (0.42, 0.20, 0.065, 1.0),
        (0.19, 0.065, 0.018, 1.0),
    )
    walnut = materials.wood(
        "Walnut assembly tiles",
        (0.10, 0.025, 0.007, 1.0),
        (0.018, 0.004, 0.001, 1.0),
    )
    polymer = materials.solid(
        "Graphite assembly trays", (0.025, 0.035, 0.04, 1.0), 0.3
    )
    add_loading_view(loading, source_parts, maple, walnut, polymer)
    add_finished_view(finished, source_parts, maple, walnut, polymer)
    for source in source_parts.values():
        bpy.data.objects.remove(source, do_unlink=True)

    loading.hide_render = True
    finished.hide_render = True
    bpy.ops.wm.save_as_mainfile(filepath=str(OUTPUT_PATH))
    render_views(loading, finished)
    print(f"Saved {OUTPUT_PATH}")


if __name__ == "__main__":
    build()
