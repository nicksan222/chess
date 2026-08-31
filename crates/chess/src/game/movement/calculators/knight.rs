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

pub(super) fn destinations(board: &Board, piece: Piece) -> SquareSet {
    shared::offset_destinations(board, piece, &OFFSETS)
}

pub(super) fn attacks(piece: Piece) -> SquareSet {
    shared::offset_attacks(piece, &OFFSETS)
}
