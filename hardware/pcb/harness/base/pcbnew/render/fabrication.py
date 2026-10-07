"""Export and package local Gerber/Excellon fabrication data from a checked PCB."""

from pathlib import Path
from typing import Protocol
from zipfile import ZIP_DEFLATED, ZipFile

from ...circuit import Circuit
from ...net import Net


class ToolRunner(Protocol):
    def __call__(self, directory: Path, *arguments: str) -> None: ...


def fabrication_layers(copper_layers: int) -> tuple[str, ...]:
    if copper_layers not in (2, 4, 6, 8):
        raise ValueError("unsupported copper layer count")
    return (
        "F.Cu",
        *(f"In{index}.Cu" for index in range(1, copper_layers - 1)),
        "B.Cu",
        "F.Mask",
        "B.Mask",
        "F.SilkS",
        "B.SilkS",
        "Edge.Cuts",
        "F.Paste",
        "B.Paste",
    )


def package_fabrication(
    directory: Path, name: str, layers: tuple[str, ...], archive: Path
) -> None:
    """Reject missing/truncated CAM data before publishing the archive."""
    for layer in layers:
        path = (
            directory
            / f"{name}-{layer.replace('.', '_').replace('_SilkS', '_Silkscreen')}.gbr"
        )
        if not path.is_file():
            raise ValueError(f"missing fabrication layer: {layer}")
        content = path.read_text()
        if "%FS" not in content or not content.rstrip().endswith("M02*"):
            raise ValueError(f"invalid Gerber layer: {layer}")
    for plating in ("PTH", "NPTH"):
        path = directory / f"{name}-{plating}.drl"
        if not path.is_file():
            raise ValueError(f"missing {plating} drill file")
        content = path.read_text()
        if not content.startswith("M48") or not content.rstrip().endswith("M30"):
            raise ValueError(f"invalid {plating} drill file")
    with ZipFile(archive, "w", ZIP_DEFLATED) as output:
        for path in sorted(directory.iterdir()):
            if path.is_file():
                output.write(path, path.name)


def write_fabrication[BoardNet: Net](
    circuit: Circuit[BoardNet],
    board: Path,
    directory: Path,
    name: str,
    pending: tuple[str, ...],
    run: ToolRunner,
) -> Path:
    layers = fabrication_layers(circuit.layout.copper_layers)
    cam = directory / "fabrication"
    cam.mkdir()
    run(
        directory,
        "kicad-cli",
        "pcb",
        "export",
        "gerbers",
        "--layers",
        ",".join(layers),
        "--no-x2",
        "--no-protel-ext",
        "--subtract-soldermask",
        "-o",
        str(cam) + "/",
        str(board),
    )
    run(
        directory,
        "kicad-cli",
        "pcb",
        "export",
        "drill",
        "--format",
        "excellon",
        "--excellon-units",
        "mm",
        "--excellon-separate-th",
        "--excellon-oval-format",
        "route",
        "--generate-report",
        "--report-path",
        str(cam / "drill-report.txt"),
        "-o",
        str(cam) + "/",
        str(board),
    )
    outline = circuit.outline
    if outline is None:
        raise ValueError("fabrication requires an outline")
    (cam / "README.txt").write_text(
        f"{name}: local fabrication export\n"
        f"Size: {outline.width_mm} x {outline.height_mm} mm\n"
        f"Thickness: {circuit.layout.thickness_mm} mm\n"
        f"Copper order, top to bottom: {', '.join(layers[: circuit.layout.copper_layers])}\n"
        "Gerbers: RS-274X. Drills: Excellon, millimetres, absolute origin, separate PTH/NPTH.\n"
        "BOM and placement CSV are provided beside this archive for assembly review.\n"
        "Before ordering, confirm material/Tg, copper weights, dielectric stackup, surface finish,\n"
        "mask/silkscreen colors and via treatment with the fabricator. An unset job finish is not bare copper.\n"
        "Check the fabricator's layer order, outline and PTH/NPTH interpretation before payment.\n"
        "Manufacturing approval remains pending:\n"
        + "".join(f"- {item}\n" for item in pending)
    )
    archive = directory / f"{name}-fabrication.zip"
    package_fabrication(cam, name, layers, archive)
    return archive
