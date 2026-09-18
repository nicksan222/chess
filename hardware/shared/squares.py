"""Physical chessboard-square placement and stable electrical identities."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from .hall_banks import FILES, SquarePosition

Point = tuple[float, float]


@dataclass(frozen=True, slots=True)
class BoardSquare:
    """One logical square and the physical features attached to it."""

    position: SquarePosition
    centre_mm: Point
    led_offset_mm: Point
    hall_offset_mm: Point
    grid_count: int

    @property
    def name(self) -> str:
        return self.position.name

    @property
    def row(self) -> int:
        return self.grid_count - 1 - self.position.rank

    @property
    def column(self) -> int:
        return self.position.file_index

    @property
    def led_position_mm(self) -> Point:
        return tuple(
            a + b for a, b in zip(self.centre_mm, self.led_offset_mm, strict=True)
        )

    @property
    def hall_position_mm(self) -> Point:
        return tuple(
            a + b for a, b in zip(self.centre_mm, self.hall_offset_mm, strict=True)
        )

    @property
    def is_dark(self) -> bool:
        return (self.row + self.column) % 2 == 1

    @property
    def led_chain_index(self) -> int:
        """Zero-based serpentine LED index, beginning at A1."""
        file_index = self.position.file_index
        rank = self.position.rank
        offset = file_index if rank % 2 == 0 else self.grid_count - 1 - file_index
        return rank * self.grid_count + offset

    @property
    def sensor_number(self) -> int:
        """Published one-based Hall reference, row-major within each 4x4 quadrant."""
        file_index = self.position.file_index
        rank = self.position.rank
        return (
            (rank // 4) * 32
            + (file_index // 4) * 16
            + (rank % 4) * 4
            + file_index % 4
            + 1
        )


@dataclass(frozen=True, slots=True)
class SquareLayout:
    """Complete physical and electrical topology for the 8x8 playing area."""

    squares: tuple[BoardSquare, ...]
    grid_count: int

    @classmethod
    def build(
        cls,
        *,
        grid_count: int,
        square_size: float,
        playing_span: float,
        led_offset_mm: Point,
        hall_offset_mm: Point,
    ) -> SquareLayout:
        if grid_count != len(FILES) or grid_count != 8:
            raise ValueError("Square layout must be exactly 8x8")
        squares = tuple(
            BoardSquare(
                position=SquarePosition(column, grid_count - 1 - row),
                centre_mm=(
                    -playing_span / 2.0 + (column + 0.5) * square_size,
                    playing_span / 2.0 - (row + 0.5) * square_size,
                ),
                led_offset_mm=led_offset_mm,
                hall_offset_mm=hall_offset_mm,
                grid_count=grid_count,
            )
            for row in range(grid_count)
            for column in range(grid_count)
        )
        layout = cls(squares, grid_count)
        layout.validate_topology()
        return layout

    def __iter__(self) -> Iterator[BoardSquare]:
        return iter(self.squares)

    def __len__(self) -> int:
        return len(self.squares)

    def by_name(self, name: str) -> BoardSquare:
        return self.by_position(SquarePosition.parse(name))

    def by_position(self, position: SquarePosition) -> BoardSquare:
        try:
            return next(
                square for square in self.squares if square.position == position
            )
        except StopIteration as error:
            raise KeyError(position.name) from error

    @property
    def led_chain(self) -> tuple[BoardSquare, ...]:
        return tuple(sorted(self.squares, key=lambda square: square.led_chain_index))

    @property
    def dark_squares(self) -> tuple[BoardSquare, ...]:
        return tuple(square for square in self.squares if square.is_dark)

    def validate_topology(self) -> None:
        if self.grid_count != len(FILES) or self.grid_count != 8:
            raise ValueError("Square layout must be exactly 8x8")
        expected = self.grid_count**2
        if len(self.squares) != expected:
            raise ValueError("Square layout must contain one entry per board square")
        if len({square.position for square in self.squares}) != expected:
            raise ValueError("Square positions must be unique")
        if len({square.centre_mm for square in self.squares}) != expected:
            raise ValueError("Square centres must be unique")
        if len({square.led_position_mm for square in self.squares}) != expected:
            raise ValueError("LED positions must be unique")
        if len({square.hall_position_mm for square in self.squares}) != expected:
            raise ValueError("Hall positions must be unique")
        if {square.led_chain_index for square in self.squares} != set(range(expected)):
            raise ValueError("LED chain indices must be contiguous and unique")
        if {square.sensor_number for square in self.squares} != set(
            range(1, expected + 1)
        ):
            raise ValueError("Hall sensor numbers must be contiguous and one-based")
        if len(self.dark_squares) != expected // 2:
            raise ValueError("A checkerboard must have half its squares dark")
