use sha2::{Digest, Sha256};

use crate::{Board, Color, PieceKind};

use super::super::HistoryHash;

const BOARD_DOMAIN: &[u8] = b"chess.board-anchor.sha256.v1\0";

pub(in crate::game::history) fn calculate_board_anchor(board: &Board) -> HistoryHash {
    let mut digest = Sha256::new();
    digest.update(BOARD_DOMAIN);
    for square in crate::Square::all() {
        digest.update([board.piece_at(square).map_or(0, |piece| {
            color_code(piece.color()) * 6 + piece_kind_code(piece.kind()) + 1
        })]);
    }
    digest.update([color_code(board.side_to_move())]);
    let rights = board.castling_rights();
    digest.update([
        rights.kingside(Color::White) as u8,
        rights.queenside(Color::White) as u8,
        rights.kingside(Color::Black) as u8,
        rights.queenside(Color::Black) as u8,
    ]);
    digest.update([board
        .en_passant_target()
        .map_or(u8::MAX, |square| square.index().value())]);
    digest.update(board.halfmove_clock().value().to_be_bytes());
    digest.update(board.fullmove_number().value().to_be_bytes());
    HistoryHash::from_bytes(digest.finalize().into())
}

const fn color_code(color: Color) -> u8 {
    match color {
        Color::White => 0,
        Color::Black => 1,
    }
}

const fn piece_kind_code(kind: PieceKind) -> u8 {
    match kind {
        PieceKind::Pawn => 0,
        PieceKind::Knight => 1,
        PieceKind::Bishop => 2,
        PieceKind::Rook => 3,
        PieceKind::Queen => 4,
        PieceKind::King => 5,
    }
}
