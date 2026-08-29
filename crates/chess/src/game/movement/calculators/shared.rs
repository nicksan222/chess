use crate::{Board, BoardDirection, FileOffset, Piece, RankOffset, SquareOffset, SquareSet};

pub(super) const DIAGONALS: [BoardDirection; 4] = [
    BoardDirection::TowardRank8FileH,
    BoardDirection::TowardRank8FileA,
    BoardDirection::TowardRank1FileH,
    BoardDirection::TowardRank1FileA,
];

pub(super) const ORTHOGONALS: [BoardDirection; 4] = [
    BoardDirection::TowardRank8,
    BoardDirection::TowardRank1,
    BoardDirection::TowardFileH,
    BoardDirection::TowardFileA,
];

pub(super) const KING_OFFSETS: [SquareOffset; 8] = [
    SquareOffset::new(FileOffset::TOWARD_H, RankOffset::ZERO),
    SquareOffset::new(FileOffset::TOWARD_H, RankOffset::TOWARD_RANK_8),
    SquareOffset::new(FileOffset::ZERO, RankOffset::TOWARD_RANK_8),
    SquareOffset::new(FileOffset::TOWARD_A, RankOffset::TOWARD_RANK_8),
    SquareOffset::new(FileOffset::TOWARD_A, RankOffset::ZERO),
    SquareOffset::new(FileOffset::TOWARD_A, RankOffset::TOWARD_RANK_1),
    SquareOffset::new(FileOffset::ZERO, RankOffset::TOWARD_RANK_1),
    SquareOffset::new(FileOffset::TOWARD_H, RankOffset::TOWARD_RANK_1),
];

pub(super) fn offset_destinations(
    board: &Board,
    piece: Piece,
    offsets: &[SquareOffset],
) -> SquareSet {
    offsets
        .iter()
        .filter_map(|offset| piece.square().offset(*offset))
        .filter(|destination| {
            board
                .piece_at(*destination)
                .is_none_or(|occupant| occupant.color() != piece.color())
        })
        .collect()
}

pub(super) fn offset_attacks(piece: Piece, offsets: &[SquareOffset]) -> SquareSet {
    offsets
        .iter()
        .filter_map(|offset| piece.square().offset(*offset))
        .collect()
}

pub(super) fn ray_destinations(
    board: &Board,
    piece: Piece,
    directions: &[BoardDirection],
) -> SquareSet {
    let mut destinations = SquareSet::EMPTY;
    for direction in directions {
        for square in piece.square().ray(*direction) {
            match board.piece_at(square) {
                None => {
                    destinations.insert(square);
                }
                Some(occupant) => {
                    if occupant.color() != piece.color() {
                        destinations.insert(square);
                    }
                    break;
                }
            }
        }
    }
    destinations
}

pub(super) fn ray_attacks(board: &Board, piece: Piece, directions: &[BoardDirection]) -> SquareSet {
    let mut attacks = SquareSet::EMPTY;
    for direction in directions {
        for square in piece.square().ray(*direction) {
            attacks.insert(square);
            if board.piece_at(square).is_some() {
                break;
            }
        }
    }
    attacks
}
