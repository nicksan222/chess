"""Export purchasing facts directly from the declared component instances."""

import csv
from enum import StrEnum
from pathlib import Path
from typing import cast

from ...circuit import Circuit
from ...component import BoardComponent
from ...net import Net


def write_bom[BoardNet: Net](circuit: Circuit[BoardNet], path: Path) -> None:
    """Write one explicit purchasing row per placed physical component."""
    circuit.validate()
    with path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(
            (
                "Reference",
                "Product",
                "Manufacturer",
                "Part number",
                "Package",
                "Datasheet",
                "Purpose",
            )
        )
        for component in circuit.components():
            if not isinstance(component, BoardComponent):
                raise ValueError("PCB BOM needs BoardComponent instances")
            part = cast(BoardComponent[StrEnum], component)
            product = part.definition.product
            writer.writerow(
                (
                    component.reference,
                    product.key,
                    product.manufacturer,
                    product.part_number,
                    product.package,
                    product.datasheet,
                    component.purpose,
                )
            )
