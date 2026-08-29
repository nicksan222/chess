use crate::{Board, Color, Piece, PieceKind, Rank, SquareOffset, SquareSet};

pub(super) fn destinations(board: &Board, piece: Piece) -> SquareSet {
    let (forward, start_rank) = movement(piece.color());
    let mut destinations = SquareSet::EMPTY;
    if let Some(one) = piece.square().offset(SquareOffset::new(0, forward))
        && board.piece_at(one).is_none()
    {
        destinations.insert(one);
        if piece.square().rank() == start_rank
            && let Some(two) = one.offset(SquareOffset::new(0, forward))
            && board.piece_at(two).is_none()
        {
            destinations.insert(two);
        }
    }

    for files in [-1, 1] {
        let Some(target) = piece.square().offset(SquareOffset::new(files, forward)) else {
            continue;
        };
        let captures_piece = board
            .piece_at(target)
            .is_some_and(|occupant| occupant.color() != piece.color());
        let captures_en_passant = board.en_passant_target() == Some(target)
            && target
                .offset(SquareOffset::new(0, -forward))
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

pub(super) fn attacks(piece: Piece) -> SquareSet {
    let (forward, _) = movement(piece.color());
    [-1, 1]
        .into_iter()
        .filter_map(|files| piece.square().offset(SquareOffset::new(files, forward)))
        .collect()
}

fn movement(color: Color) -> (i8, Rank) {
    match color {
        Color::White => (1, Rank::Two),
        Color::Black => (-1, Rank::Seven),
    }
}
