"""Compact Hall-bank ownership, channel order, address straps, and labels."""

from dataclasses import dataclass

FILES = "ABCDEFGH"
BANK_FILES = 4
BANK_RANKS = 2
_BANK_HALF_FILES = BANK_FILES // 2


@dataclass(frozen=True, order=True, slots=True)
class SquarePosition:
    """A square's zero-based file and rank coordinates."""

    file_index: int
    rank: int

    def __post_init__(self) -> None:
        if self.file_index not in range(len(FILES)) or self.rank not in range(
            len(FILES)
        ):
            raise ValueError(
                f"invalid square coordinates {(self.file_index, self.rank)}"
            )

    @classmethod
    def parse(cls, name: str) -> "SquarePosition":
        """Parse standard chess notation without exposing its string encoding."""
        text = name.strip().upper()
        if len(text) < 2 or text[0] not in FILES:
            raise ValueError(f"invalid square {name!r}")
        try:
            return cls(FILES.index(text[0]), int(text[1:]) - 1)
        except ValueError as error:
            raise ValueError(f"invalid square {name!r}") from error

    @property
    def name(self) -> str:
        return f"{FILES[self.file_index]}{self.rank + 1}"


@dataclass(frozen=True)
class HallBank:
    index: int
    first_file: int
    first_rank: int

    @property
    def members(self) -> tuple[SquarePosition, ...]:
        """P0–P3 serve the left half; P4–P7 the right, matching SOIC sides."""
        return tuple(
            SquarePosition(
                self.first_file + half * _BANK_HALF_FILES + column,
                self.first_rank + row,
            )
            for half in range(2)
            for row in range(BANK_RANKS)
            for column in range(_BANK_HALF_FILES)
        )

    @property
    def label(self) -> str:
        first = SquarePosition(self.first_file, self.first_rank)
        last = SquarePosition(
            self.first_file + BANK_FILES - 1,
            self.first_rank + BANK_RANKS - 1,
        )
        return f"{first.name}-{last.name}"

    @property
    def address(self) -> int:
        return 0x20 + self.index

    @property
    def straps(self) -> tuple[bool, bool, bool]:
        """A0, A1, A2; true is VCC and false is GND."""
        return tuple(bool(self.index & (1 << bit)) for bit in range(3))

    def centre(self, pitch: float, span: float) -> tuple[float, float]:
        return (
            (self.first_file + BANK_FILES / 2) * pitch - span / 2,
            (self.first_rank + BANK_RANKS / 2) * pitch - span / 2,
        )


def banks(grid_count: int) -> tuple[HallBank, ...]:
    return tuple(
        HallBank(index, file_index, rank)
        for index, (file_index, rank) in enumerate(
            (file_index, rank)
            for rank in range(0, grid_count, BANK_RANKS)
            for file_index in range(0, grid_count, BANK_FILES)
        )
    )
