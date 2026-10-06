"""Small lifecycle helpers shared by code-authored Blender projects.

Role: the steps every printable project's generator repeats: parse the output
directory Blender was given, create a clean scene with the standard collections,
record metadata on the scene, and finally validate, save and render. Keeping them here
means each `generate.py` only describes its own geometry.
"""

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

import bpy

from core import modeling, presentation, validation

# Value types Blender can store as custom (ID) properties on a scene.
SceneProperty = bool | int | float | str
# Scene properties that record a printed part's mesh volume.
VolumeProperty = Literal["case_volume_mm3", "plate_volume_mm3"]


class SceneMetadata(Protocol):
    """Typed project metadata that can be persisted as Blender ID properties."""

    def apply_to(self, scene: bpy.types.Scene) -> None: ...


@dataclass(frozen=True, slots=True)
class PrintableScene:
    """Named scene resources; unlike a tuple, collection roles cannot be swapped.

    `printable` holds the part that will be printed, `construction` the cutters and
    helpers used to make it (hidden from render), `studio` the floor, camera and lights.
    """

    scene: bpy.types.Scene
    printable: bpy.types.Collection
    construction: bpy.types.Collection
    studio: bpy.types.Collection


def set_scene_property(scene: bpy.types.Scene, name: str, value: SceneProperty) -> None:
    """Keep Blender's dynamic ID-property API behind one typed boundary."""
    scene[name] = value


def apply_metadata(scene: bpy.types.Scene, metadata: SceneMetadata) -> None:
    """Write a project's typed metadata onto the scene so it is saved in the .blend."""
    metadata.apply_to(scene)


def output_directory(default: Path) -> Path:
    """Read the optional output directory passed after Blender's `--` marker.

    Blender ignores arguments after `--`, so `build.py` passes the staging directory
    there. Without one (running a generator by hand) `default` is used.
    """
    if "--" not in sys.argv:
        return default
    arguments = sys.argv[sys.argv.index("--") + 1 :]
    if len(arguments) != 1:
        raise RuntimeError("CAD generator expects exactly one output directory")
    return Path(arguments[0]).resolve()


def setup_printable(
    scene_name: str,
    scale_length: float,
) -> PrintableScene:
    """Create the common scene and collections for one printable project.

    `scale_length` is the Blender unit scale (shared `BLENDER_SCALE_LENGTH`), so one
    unit reads as a millimetre. The render is 1200 x 900 on a near-black background.
    """
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
    return PrintableScene(scene, printable, construction, studio)


def save_printable(
    part: bpy.types.Object,
    build_volume_mm: tuple[float, float, float],
    output_directory: Path,
    project_name: str,
    volume_property: VolumeProperty,
) -> Path:
    """Validate, save, and render one printable project.

    Validation comes first so an invalid mesh (invalid mesh data, non-manifold, zero volume,
    too big for `build_volume_mm`) fails the build before anything is published. Writes
    `<project_name>.blend` and `<project_name>.png`, and records the mesh volume under
    `volume_property`. Returns the .blend path.
    """
    validation.validate_fdm_part(part, build_volume_mm)
    bpy.context.scene[volume_property] = part["mesh_volume_mm3"]
    output_directory.mkdir(parents=True, exist_ok=True)
    model_path = output_directory / f"{project_name}.blend"
    bpy.ops.wm.save_as_mainfile(filepath=str(model_path))
    bpy.context.scene.render.filepath = str(output_directory / f"{project_name}.png")
    bpy.ops.render.render(write_still=True)
    return model_path
