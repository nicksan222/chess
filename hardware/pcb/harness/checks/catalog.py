"""Connect this board's explicit catalog to reusable harness checks.

Only this adapter imports the board catalog. Check implementations accept
definitions or registries explicitly, so another board can use them too.
"""

from pcb.components.catalog import PCB_DEFINITIONS
from shared.components import APPROVED_COMPONENTS
from shared.components.oled_module import OLED_REFERENCE_DOCUMENTS


def datasheet_references() -> tuple[tuple[str, str], ...]:
    """Include purchasing parts, wire spools, and rendered product references."""
    return (
        tuple((part.key, part.datasheet) for part in APPROVED_COMPONENTS)
        + tuple(
            (definition.product.key, definition.product.datasheet)
            for definition in PCB_DEFINITIONS
        )
        + tuple(
            ("OLED_MODULE supporting reference", url)
            for url in OLED_REFERENCE_DOCUMENTS
        )
    )
