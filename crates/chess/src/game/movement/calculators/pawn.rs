//! Pawn pushes, captures, attacks, and en-passant calculation.

use crate::{
    Board, Color, FileOffset, Piece, PieceKind, Rank, RankOffset, SquareOffset, SquareSet,
};

/// Pawn pushes, captures, and en-passant candidates for the side to move.
///
/// Single pushes require an empty square; double pushes additionally require
/// the start rank and two empty squares. Diagonal targets need an enemy piece
/// or a legal en-passant target. King safety is filtered later by
/// [`Board::legal_destinations`](crate::Board::legal_destinations).
pub(super) fn destinations(board: &Board, piece: Piece) -> SquareSet {
    let (forward, start_rank) = movement(piece.color());
    let mut destinations = SquareSet::EMPTY;
    if let Some(one) = piece
        .square()
        .offset(SquareOffset::new(FileOffset::ZERO, forward))
        && board.piece_at(one).is_none()
    {
        destinations.insert(one);
        if piece.square().rank() == start_rank
            && let Some(two) = one.offset(SquareOffset::new(FileOffset::ZERO, forward))
            && board.piece_at(two).is_none()
        {
            destinations.insert(two);
        }
    }

    for files in [FileOffset::TOWARD_A, FileOffset::TOWARD_H] {
        let Some(target) = piece.square().offset(SquareOffset::new(files, forward)) else {
            continue;
        };
        let captures_piece = board
            .piece_at(target)
            .is_some_and(|occupant| occupant.color() != piece.color());
        let captures_en_passant = board.en_passant_target() == Some(target)
            && target
                .offset(SquareOffset::new(FileOffset::ZERO, forward.reversed()))
                .and_then(|captured| board.piece_at(captured))
                .is_some_and(|captured| {
                    captured.color() != piece.color() && captured.kind() == PieceKind::Pawn
                });
        if captures_piece || captures_en_passant {
            destinations.insert(target);
        }
    }
    destinations
}

/// Diagonal pawn attack squares, regardless of occupancy.
///
/// Used for check detection rather than move candidates, so empty squares
/// and own-occupied squares are still reported as attacked.
pub(super) fn attacks(piece: Piece) -> SquareSet {
    let (forward, _) = movement(piece.color());
    [FileOffset::TOWARD_A, FileOffset::TOWARD_H]
        .into_iter()
        .filter_map(|files| piece.square().offset(SquareOffset::new(files, forward)))
        .collect()
}

fn movement(color: Color) -> (RankOffset, Rank) {
    let start_rank = match color {
        Color::White => Rank::Two,
        Color::Black => Rank::Seven,
    };
    (RankOffset::pawn_push(color), start_rank)
}
