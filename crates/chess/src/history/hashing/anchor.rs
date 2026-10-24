//! Canonical hashing of the board that anchors a game history.

use crate::{Board, Color, PieceKind};

use super::{
    super::HistoryHash,
    writer::{HashWriter, color_code},
};

const BOARD_DOMAIN: &[u8] = b"chess.board-anchor.sha256.v1\0";

/// Computes the board commitment that anchors a game timeline.
///
/// The anchor canonically hashes every square's piece, the side to move,
/// castling rights, the en passant target, and both move clocks under a
/// board-anchor domain. A [`GameHistory`](crate::GameHistory) built with
/// [`GameHistory::for_board`](crate::GameHistory::for_board) stores this
/// value as both anchor and initial tip, and
/// [`GameHistory::verify`](crate::GameHistory::verify) replays the hash
/// chain starting from it, so divergent initial boards fail as a
/// previous-hash mismatch on the first [`Ply`](crate::Ply).
pub(in crate::history) fn calculate_board_anchor(board: &Board) -> HistoryHash {
    let mut writer = HashWriter::new(BOARD_DOMAIN);
    for square in crate::Square::all() {
        writer.byte(board.piece_at(square).map_or(0, |piece| {
            color_code(piece.color()) * 6 + piece_kind_code(piece.kind()) + 1
        }));
    }
    writer.color(board.side_to_move());
    let rights = board.castling_rights();
    writer
        .byte(u8::from(rights.kingside(Color::White)))
        .byte(u8::from(rights.queenside(Color::White)))
        .byte(u8::from(rights.kingside(Color::Black)))
        .byte(u8::from(rights.queenside(Color::Black)))
        .byte(
            board
                .en_passant_target()
                .map_or(u8::MAX, |square| square.index().value()),
        )
        .bytes(&board.halfmove_clock().value().to_be_bytes())
        .bytes(&board.fullmove_number().value().to_be_bytes());
    writer.finish()
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
