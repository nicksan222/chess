"""Small lifecycle helpers shared by code-authored Blender projects."""

import sys
from pathlib import Path

import bpy

from core import modeling, presentation, validation


def output_directory(default: Path) -> Path:
    """Read the optional output directory passed after Blender's `--` marker."""
    if "--" not in sys.argv:
        return default
    arguments = sys.argv[sys.argv.index("--") + 1 :]
    if len(arguments) != 1:
        raise RuntimeError("CAD generator expects exactly one output directory")
    return Path(arguments[0]).resolve()


def setup_printable(
    scene_name: str,
    scale_length: float,
) -> tuple[
    bpy.types.Scene,
    bpy.types.Collection,
    bpy.types.Collection,
    bpy.types.Collection,
]:
    """Create the common scene and collections for one printable project."""
    modeling.clear_scene()
    scene = presentation.configure_scene(
        scene_name,
        scale_length,
        (1200, 900),
        (0.02, 0.025, 0.035, 1.0),
        0.28,
    )
    printable = modeling.new_collection("PRINTABLE_PART")
    construction = modeling.new_collection("CONSTRUCTION")
    studio = modeling.new_collection("PRESENTATION")
    return scene, printable, construction, studio


def save_printable(
    part: bpy.types.Object,
    build_volume_mm: tuple[float, float, float],
    output_directory: Path,
    project_name: str,
    volume_property: str,
) -> Path:
    """Validate, save, and render one printable project."""
    validation.validate_fdm_part(part, build_volume_mm)
    bpy.context.scene[volume_property] = part["mesh_volume_mm3"]
    output_directory.mkdir(parents=True, exist_ok=True)
    model_path = output_directory / f"{project_name}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(model_path))
    bpy.context.scene.render.filepath = str(output_directory / f"{project_name}.png")
    bpy.ops.render.render(write_still=True)
    return model_path
