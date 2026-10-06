"""Typed native PCB part binding and registry validation.

Role: `PcbPart` ties one approved product (`ComponentSpec`) to its typed pin model and
its native footprint template, plus the display defaults shown in the BOM and
schematic. `parts/catalog.py` lists every binding and `native.place()` consumes them.
Validating at construction (import) time means an inconsistent binding fails
immediately rather than producing a quietly wrong board.
"""

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

import pcbnew

from shared.components import ComponentSpec
from shared.electronics import EndpointResolver


class DrawingView(Enum):
    """Which side the template's land drawing is seen from.

    MOUNTING_SIDE: the datasheet layout as seen from the side the part sits on
    (KiCad and most catalogues, e.g. JST VH p4 note 1). On the bottom it needs a
    true mirror flip. BOARD_TOP: holes defined by a mating part seen from the
    board top (the Pi header), so a bottom placement keeps them unmirrored.
    """

    MOUNTING_SIDE = "mounting side"
    BOARD_TOP = "board top"


@dataclass(frozen=True)
class PcbPart[Part: EndpointResolver]:
    """One approved product's logical model, land pattern, and display defaults."""

    spec: ComponentSpec  # Approved product: MPN, package, body, datasheet.
    model: Callable[[str], Part]  # Pin model class; called with a reference designator.
    template: pcbnew.FOOTPRINT  # Native footprint copied for each placement.
    library: str  # Short library label stored on the footprint.
    nominal_value: str  # Default displayed value; placement may override.
    default_purpose: str  # Default role text; placement may override.
    drawing_view: DrawingView  # Side the land drawing is seen from (bottom flips).

    def __post_init__(self) -> None:
        # Three guards: display text present; the template's Package field equals the
        # approved product's package (wrong footprint for the part); and the pin model
        # actually supports this product key (wrong pinout for the part).
        if not all((self.library, self.nominal_value, self.default_purpose)):
            raise ValueError(f"{self.spec.key}: PCB display defaults must not be empty")
        if self.template.GetFieldText("Package") != self.spec.package:
            raise ValueError(
                f"{self.spec.key}: footprint package does not match product"
            )
        if not self.model("REGISTRY_CHECK").supports_part_key(self.spec.key):
            raise ValueError(
                f"{self.spec.key}: electronic model does not support product"
            )

    def new_model(self, reference: str) -> Part:
        """Construct the typed logical model selected by this registry entry."""
        return self.model(reference)
