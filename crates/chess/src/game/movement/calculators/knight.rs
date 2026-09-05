//! Knight destinations and attacked-square calculation.

use crate::{Board, FileOffset, Piece, RankOffset, SquareOffset, SquareSet};

use super::shared;

const OFFSETS: [SquareOffset; 8] = [
    SquareOffset::new(FileOffset::TOWARD_H, RankOffset::TOWARD_RANK_8.doubled()),
    SquareOffset::new(FileOffset::TOWARD_H.doubled(), RankOffset::TOWARD_RANK_8),
    SquareOffset::new(FileOffset::TOWARD_H.doubled(), RankOffset::TOWARD_RANK_1),
    SquareOffset::new(FileOffset::TOWARD_H, RankOffset::TOWARD_RANK_1.doubled()),
    SquareOffset::new(FileOffset::TOWARD_A, RankOffset::TOWARD_RANK_1.doubled()),
    SquareOffset::new(FileOffset::TOWARD_A.doubled(), RankOffset::TOWARD_RANK_1),
    SquareOffset::new(FileOffset::TOWARD_A.doubled(), RankOffset::TOWARD_RANK_8),
    SquareOffset::new(FileOffset::TOWARD_A, RankOffset::TOWARD_RANK_8.doubled()),
];

/// Knight step-offset candidates that avoid friendly occupancy.
///
/// Knights leap, so blockers are irrelevant. King safety is filtered later by
/// [`Board::legal_destinations`](crate::Board::legal_destinations).
pub(super) fn destinations(board: &Board, piece: Piece) -> SquareSet {
    shared::offset_destinations(board, piece, &OFFSETS)
}

/// Knight attack squares, regardless of occupancy.
///
/// Used by check detection; see [`super::is_attacked`].
pub(super) fn attacks(piece: Piece) -> SquareSet {
    shared::offset_attacks(piece, &OFFSETS)
}
