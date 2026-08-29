use super::{File, FileOffset, Rank, RankOffset, Square, SquareOffset};

/// One of the four objective chessboard edges.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum BoardEdge {
    /// The `a`-file edge.
    FileA,
    /// The `h`-file edge.
    FileH,
    /// The rank-1 edge.
    Rank1,
    /// The rank-8 edge.
    Rank8,
}

impl BoardEdge {
    /// Every edge in file-then-rank order.
    pub const ALL: [Self; 4] = [Self::FileA, Self::FileH, Self::Rank1, Self::Rank8];

    /// Returns whether this edge contains `square`.
    #[must_use]
    pub const fn contains(self, square: Square) -> bool {
        matches!(
            (self, square.file(), square.rank()),
            (Self::FileA, File::A, _)
                | (Self::FileH, File::H, _)
                | (Self::Rank1, _, Rank::One)
                | (Self::Rank8, _, Rank::Eight)
        )
    }
}

/// One of the eight straight or diagonal coordinate directions.
///
/// Names refer to fixed files and ranks, never to a player's perspective.
#[derive(Clone, Copy, Debug, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub enum BoardDirection {
    /// Toward rank 8.
    TowardRank8,
    /// Toward rank 1.
    TowardRank1,
    /// Toward file `h`.
    TowardFileH,
    /// Toward file `a`.
    TowardFileA,
    /// Toward rank 8 and file `h`.
    TowardRank8FileH,
    /// Toward rank 8 and file `a`.
    TowardRank8FileA,
    /// Toward rank 1 and file `h`.
    TowardRank1FileH,
    /// Toward rank 1 and file `a`.
    TowardRank1FileA,
}

impl BoardDirection {
    pub(super) const fn offset(self) -> SquareOffset {
        match self {
            Self::TowardRank8 => SquareOffset::new(FileOffset::ZERO, RankOffset::TOWARD_RANK_8),
            Self::TowardRank1 => SquareOffset::new(FileOffset::ZERO, RankOffset::TOWARD_RANK_1),
            Self::TowardFileH => SquareOffset::new(FileOffset::TOWARD_H, RankOffset::ZERO),
            Self::TowardFileA => SquareOffset::new(FileOffset::TOWARD_A, RankOffset::ZERO),
            Self::TowardRank8FileH => {
                SquareOffset::new(FileOffset::TOWARD_H, RankOffset::TOWARD_RANK_8)
            }
            Self::TowardRank8FileA => {
                SquareOffset::new(FileOffset::TOWARD_A, RankOffset::TOWARD_RANK_8)
            }
            Self::TowardRank1FileH => {
                SquareOffset::new(FileOffset::TOWARD_H, RankOffset::TOWARD_RANK_1)
            }
            Self::TowardRank1FileA => {
                SquareOffset::new(FileOffset::TOWARD_A, RankOffset::TOWARD_RANK_1)
            }
        }
    }
}
