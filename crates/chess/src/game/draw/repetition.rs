//! Exact position identity and repetition counting from authoritative history.

use crate::{
    Board, CastlingRights, Color, FileOffset, GameHistory, HistoryEvent, PieceKind, RankOffset,
    Square, SquareOffset,
};

/// Exact, collision-free piece placement using four bits per square.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct PiecePlacement([u64; 4]);

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
struct PositionKey {
    placement: PiecePlacement,
    side_to_move: Color,
    castling_rights: CastlingRights,
    en_passant_target: Option<Square>,
}

pub(super) fn count(initial_board: Board, history: &GameHistory, current_board: &Board) -> u8 {
    let target = PositionKey::new(current_board);
    let mut board = initial_board;
    let mut repetitions = u8::from(PositionKey::new(&board) == target);

    for step in history.iter() {
        let HistoryEvent::Move(chess_move) = step.event() else {
            continue;
        };
        board
            .make_move(chess_move)
            .expect("accepted move events replay from the initial board");
        repetitions = repetitions.saturating_add(u8::from(PositionKey::new(&board) == target));
    }
    repetitions
}

impl PiecePlacement {
    fn new(board: &Board) -> Self {
        let mut words = [0_u64; 4];
        for square in Square::all() {
            let Some(piece) = board.piece_at(square) else {
                continue;
            };
            let index = square.index().value();
            let word = (index / 16) as usize;
            let shift = u32::from((index % 16) * 4);
            let code = piece_code(piece.color(), piece.kind());
            debug_invariant!(code < 16, "a piece code must fit in four bits");
            words[word] |= u64::from(code) << shift;
        }
        Self(words)
    }
}

impl PositionKey {
    fn new(board: &Board) -> Self {
        Self {
            placement: PiecePlacement::new(board),
            side_to_move: board.side_to_move(),
            castling_rights: board.castling_rights(),
            en_passant_target: effective_en_passant_target(board),
        }
    }
}

const fn piece_code(color: Color, kind: PieceKind) -> u8 {
    let color_offset = match color {
        Color::White => 0,
        Color::Black => 6,
    };
    let kind = match kind {
        PieceKind::Pawn => 1,
        PieceKind::Knight => 2,
        PieceKind::Bishop => 3,
        PieceKind::Rook => 4,
        PieceKind::Queen => 5,
        PieceKind::King => 6,
    };
    color_offset + kind
}

fn effective_en_passant_target(board: &Board) -> Option<Square> {
    let target = board.en_passant_target()?;
    let side = board.side_to_move();
    let toward_source = RankOffset::pawn_push(side).reversed();
    [FileOffset::TOWARD_A, FileOffset::TOWARD_H]
        .into_iter()
        .filter_map(|file| target.offset(SquareOffset::new(file, toward_source)))
        .filter_map(|source| board.piece_at(source))
        .filter(|piece| piece.color() == side && piece.kind() == PieceKind::Pawn)
        .any(|pawn| board.legal_destinations(pawn).contains(target))
        .then_some(target)
}
