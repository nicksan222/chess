"""Compact Hall-bank ownership, channel order, address straps, and labels.

Role: the single source of truth for which squares each Hall-sensor GPIO expander
("bank") reads, which expander channel (P0-P7) each square uses, and each bank's
I2C address. `dimensions/board.py` builds `HALL_BANKS` from `banks()`; `wiring.py`,
the PCB assemblies must agree with it, as must the host acquisition contract in
`docs/host.md` (not yet implemented in `apps/firmware`).

Compact 4x2 banks: each bank serves a 4-file x 2-rank block (8 squares = the 8
expander channels). Design rationale (not stated in the repo docs): keeping a
bank's sensors adjacent should keep its sense nets short. Changing the block
shape changes the channel order and the PCB routing together.
"""

from dataclasses import dataclass

# Chess file letters, a-file first. Also fixes the 8x8 grid size used for validation.
FILES = "ABCDEFGH"
# A bank is a 4-file x 2-rank block of squares (8 squares = the 8 expander pins).
BANK_FILES = 4
BANK_RANKS = 2
# The expander package has one pin bank per side, so a bank splits into a left and
# a right half of this many files each (see HallBank.members).
_BANK_HALF_FILES = BANK_FILES // 2


@dataclass(frozen=True, order=True, slots=True)
class SquarePosition:
    """A square's zero-based file and rank coordinates.

    `file_index` 0 is the A file and `rank` 0 is rank 1 (White's back rank), so
    A1 is (0, 0). Hashable and ordered so squares can key dicts and sort stably.
    """

    file_index: int
    rank: int

    def __post_init__(self) -> None:
        # Reject out-of-board coordinates at construction so no later code needs to.
        if self.file_index not in range(len(FILES)) or self.rank not in range(
            len(FILES)
        ):
            raise ValueError(
                f"invalid square coordinates {(self.file_index, self.rank)}"
            )

    @classmethod
    def parse(cls, name: str) -> "SquarePosition":
        """Parse standard chess notation without exposing its string encoding.

        Case-insensitive and whitespace-tolerant ("e4", " E4 "); anything else,
        including an out-of-range rank, raises ValueError.
        """
        text = name.strip().upper()
        if len(text) < 2 or text[0] not in FILES:
            raise ValueError(f"invalid square {name!r}")
        try:
            return cls(FILES.index(text[0]), int(text[1:]) - 1)
        except ValueError as error:
            raise ValueError(f"invalid square {name!r}") from error

    @property
    def name(self) -> str:
        """Standard notation, e.g. "E4"; used in net names and references."""
        return f"{FILES[self.file_index]}{self.rank + 1}"


@dataclass(frozen=True)
class HallBank:
    """One GPIO expander and the 4x2 block of squares whose Hall sensors it reads.

    `first_file`/`first_rank` locate the block's lower-left square; `index` orders
    banks (rank-major, see `banks()`) and also selects the I2C address straps.
    """

    index: int
    first_file: int
    first_rank: int

    @property
    def members(self) -> tuple[SquarePosition, ...]:
        """P0–P3 serve the left half; P4–P7 the right, matching SOIC sides.

        The tuple position is the expander channel number (P-port index), so this
        order is a contract with the PCB wiring and the host contract in `docs/host.md`.
        """
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
        """Diagonal-corner name such as "A1-D2"; used in sheet and file names."""
        first = SquarePosition(self.first_file, self.first_rank)
        last = SquarePosition(
            self.first_file + BANK_FILES - 1,
            self.first_rank + BANK_RANKS - 1,
        )
        return f"{first.name}-{last.name}"

    @property
    def address(self) -> int:
        """7-bit I2C address: base 0x20 plus the bank index (A0-A2 straps).

        Must match `straps` and the 0x20-0x27 map in `docs/host.md`.
        """
        return 0x20 + self.index

    @property
    def straps(self) -> tuple[bool, bool, bool]:
        """A0, A1, A2; true is VCC and false is GND.

        The strap bits are the binary digits of `index`, so each bank gets a
        unique address on the shared bus without any jumpers or configuration.
        """
        return (
            bool(self.index & 0b001),
            bool(self.index & 0b010),
            bool(self.index & 0b100),
        )

    def centre(self, pitch: float, span: float) -> tuple[float, float]:
        """Block centre in board mm (origin at board centre, Y up).

        `pitch` is the square size and `span` the playing-area width, passed in so
        this module stays free of the dimensions package (no import cycle).
        """
        return (
            (self.first_file + BANK_FILES / 2) * pitch - span / 2,
            (self.first_rank + BANK_RANKS / 2) * pitch - span / 2,
        )


def banks(grid_count: int) -> tuple[HallBank, ...]:
    """Tile the grid with banks, left to right then bottom to top.

    Bank order is the bank index, hence the address; reordering renumbers the
    expanders on the real board.
    """
    return tuple(
        HallBank(index, file_index, rank)
        for index, (file_index, rank) in enumerate(
            (file_index, rank)
            for rank in range(0, grid_count, BANK_RANKS)
            for file_index in range(0, grid_count, BANK_FILES)
        )
    )
