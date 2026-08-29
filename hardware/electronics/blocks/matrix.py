"""8x8 reed matrix: reusable square cells plus column buses."""

from __future__ import annotations

from blocks.square import add_column_pullup, add_reed_cell
from core.canvas import Schematic
from core.names import square


def add_matrix(
    sch: Schematic,
    *,
    origin_x: float = 163.0,
    origin_y: float = 114.0,
    pitch_x: float = 15.0,
    pitch_y: float = 5.0,
    files: int = 8,
    ranks: int = 8,
) -> None:
    col_x = [origin_x + file_index * pitch_x for file_index in range(files)]
    row_y = [origin_y + rank * pitch_y for rank in range(ranks)]
    col_top = origin_y - 5.0

    for file_index in range(files):
        bus_x = col_x[file_index] - 0.9
        for rank in range(ranks):
            add_reed_cell(
                sch,
                square_name=square(file_index, rank),
                reed_ref=f"SW{2 + file_index + rank * files}",
                diode_ref=f"D{2 + file_index + rank * files}",
                col_x=col_x[file_index],
                y=row_y[rank],
                row_net=f"ROW_{rank}",
            )
        add_column_pullup(
            sch,
            ref=f"R{6 + file_index}",
            col_x=col_x[file_index],
            y=col_top,
            col_net=f"COL_{file_index}",
            # No column index here: which column a part serves is the reference's
            # job, and an index would split one BOM line into eight.
            description="Matrix column pull-up to 3.3 V",
        )
        # One segment per square so every cell tap joins the same column net.
        previous = (bus_x, col_top)
        for rank in range(ranks):
            current = (bus_x, row_y[rank])
            sch.wire(*previous, *current)
            previous = current
