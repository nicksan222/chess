"""Give a board-area SVG a readable substrate without altering its copper."""

import xml.etree.ElementTree as ET
from pathlib import Path


def prepare_svg(path: Path, side: str) -> None:
    ET.register_namespace("", "http://www.w3.org/2000/svg")
    tree = ET.parse(path)
    root = tree.getroot()
    x, y, width, height = root.attrib["viewBox"].split()
    namespace = "{http://www.w3.org/2000/svg}"
    background = ET.Element(
        namespace + "rect",
        {"x": x, "y": y, "width": width, "height": height, "fill": "#164936"},
    )
    title = root.find(namespace + "title")
    if title is not None:
        title.text = f"PCB {side} copper and assembly markings"
    root.insert(0, background)
    tree.write(path, encoding="utf-8", xml_declaration=True)
