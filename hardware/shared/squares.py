"""Physical chessboard-square placement and stable electrical identities.

Role: builds the 8x8 `SquareLayout` that dimensions, PCB assemblies and CAD all
consume, so a square's centre, LED/Hall offsets, LED chain position and published
sensor number are computed in exactly one place. Coordinates are board millimetres,
origin at the playing-area centre, Y up (rank 8 at the top).
"""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass

from .hall_banks import FILES, SquarePosition

# (x, y) in millimetres.
Point = tuple[float, float]


@dataclass(frozen=True, slots=True)
class BoardSquare:
    """One logical square and the physical features attached to it.

    The LED and Hall sensor are not at the square centre by default; their
    offsets are applied on top of `centre_mm` so shared dimensions can move them
    without touching the layout algorithm.
    """

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
        """Row counted from the top of the board (rank 8 is row 0), as drawn.

        Beware: firmware's `BoardPosition.row` uses the opposite convention
        (row 0 = rank 1; see `apps/firmware/src/hardware/events/piece.rs`).
        """
        return self.grid_count - 1 - self.position.rank

    @property
    def column(self) -> int:
        return self.position.file_index

    @property
    def led_position_mm(self) -> Point:
        """Absolute LED centre: square centre plus the shared LED offset."""
        return (
            self.centre_mm[0] + self.led_offset_mm[0],
            self.centre_mm[1] + self.led_offset_mm[1],
        )

    @property
    def hall_position_mm(self) -> Point:
        """Absolute Hall sensor centre: square centre plus the shared Hall offset."""
        return (
            self.centre_mm[0] + self.hall_offset_mm[0],
            self.centre_mm[1] + self.hall_offset_mm[1],
        )

    @property
    def is_dark(self) -> bool:
        """True for dark squares (A1 is dark, as on a real board)."""
        return (self.row + self.column) % 2 == 1

    @property
    def led_chain_index(self) -> int:
        """Zero-based serpentine LED index, beginning at A1.

        Zero-based ranks 0, 2, ... (chess ranks 1, 3, ...) run A->H and the others
        H->A, so consecutive LEDs are always
        neighbours and each data/clock hop is a short link instead of a long
        return trace at the end of every rank.
        """
        file_index = self.position.file_index
        rank = self.position.rank
        offset = file_index if rank % 2 == 0 else self.grid_count - 1 - file_index
        return rank * self.grid_count + offset

    @property
    def sensor_number(self) -> int:
        """Published one-based Hall reference, row-major within each 4x4 quadrant.

        Quadrants are numbered rank-half first (ranks 1-4 then 5-8), then file-half.
        This is the user-facing sensor label, independent of expander channels.
        """
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
    """Complete physical and electrical topology for the 8x8 playing area.

    Always validated on construction through `build()`, so holding a layout means
    positions, chain indices and sensor numbers are already known to be sound.
    """

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
        """Create the layout from shared dimensions.

        `square_size` is the pitch, `playing_span` the full playing width. Rows
        run top to bottom (y decreases) while ranks run bottom to top, hence the
        `grid_count - 1 - row` rank flip.
        """
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
        """Look up a square by notation such as "E4"; raises KeyError if absent."""
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
        """Squares in electrical LED order (the daisy-chain order, A1 first)."""
        return tuple(sorted(self.squares, key=lambda square: square.led_chain_index))

    @property
    def dark_squares(self) -> tuple[BoardSquare, ...]:
        """The 32 dark squares (half the board, as on a checkerboard)."""
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
