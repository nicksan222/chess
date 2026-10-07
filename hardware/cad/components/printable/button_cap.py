"""One removable printed cap fitted to a real PCB switch actuator."""

from __future__ import annotations

from typing import TYPE_CHECKING

from cad.harness.base.component import PrintableComponent
from shared import dimensions as d
from shared.panel_buttons import PanelButton

if TYPE_CHECKING:
    import bpy


class ButtonCap(PrintableComponent):
    fit_check = True
    volume_property = "cap_volume_mm3"

    def __init__(self, button: PanelButton) -> None:
        super().__init__(f"Cap_{button.switch_reference}")
        self.button = button
        self.output_name = f"button-cap-{button.name.lower()}"
        self.scene_name = f"Printable {button.name} Button Cap"
        x, y = button.position_mm
        self.camera_location = (x + 25, y - 30, 55)
        self.camera_target = (x, y, 31)

    def build(
        self,
        collection: bpy.types.Collection,
        construction: bpy.types.Collection,
        palette: dict[str, bpy.types.Material],
    ) -> tuple[bpy.types.Object, ...]:
        from cad.harness.base.blender import materials, modeling

        x, y = self.button.position_mm
        size = d.PANEL_BUTTON_CAP_SIZE_MM
        cap = modeling.rounded_box(
            self.reference,
            size,
            (x, y, d.PANEL_BUTTON_CAP_BOTTOM_Z_MM + size[2] / 2),
            1.0,
            collection,
        )
        socket = modeling.cylinder_between(
            "Cap stem socket",
            d.PANEL_BUTTON_CAP_SOCKET_DIAMETER_MM,
            (x, y),
            d.PANEL_BUTTON_CAP_BOTTOM_Z_MM - d.BOOLEAN_RECESS_OVERLAP_MM,
            d.PANEL_BUTTON_CAP_SOCKET_TOP_Z_MM,
            construction,
            vertices=32,
        )
        modeling.cut_batch(cap, [socket], "Cap actuator socket")
        cap.data.materials.append(
            materials.solid("Control caps", (0.035, 0.045, 0.05, 1), 0.4)
        )
        cap["switch_reference"] = self.button.switch_reference
        cap["physical_reference"] = self.reference
        return (cap,)
