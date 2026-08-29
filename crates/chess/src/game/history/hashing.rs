use sha2::{Digest, Sha256};

use crate::{Board, ChessMove, Color, PieceKind};

use super::{HistoryError, MoveHash, MoveStep, Ply};

const HASH_DOMAIN: &[u8] = b"chess.move-chain.sha256.v1\0";
const BOARD_DOMAIN: &[u8] = b"chess.board-anchor.sha256.v1\0";

pub(super) fn validate_step(
    step: MoveStep,
    expected_ply: Ply,
    expected_previous: MoveHash,
) -> Result<(), HistoryError> {
    if step.ply() != expected_ply {
        return Err(HistoryError::Ply {
            expected: expected_ply,
            actual: step.ply(),
        });
    }
    if step.previous_hash() != expected_previous {
        return Err(HistoryError::PreviousHash {
            ply: step.ply(),
            expected: expected_previous,
            actual: step.previous_hash(),
        });
    }
    let expected_hash = calculate_hash(expected_previous, expected_ply, step.chess_move());
    if step.hash() != expected_hash {
        return Err(HistoryError::Hash {
            ply: step.ply(),
            expected: expected_hash,
            actual: step.hash(),
        });
    }
    Ok(())
}

pub(super) fn calculate_board_anchor(board: &Board) -> MoveHash {
    let mut digest = Sha256::new();
    digest.update(BOARD_DOMAIN);
    for square in crate::Square::all() {
        let code = match board.piece_at(square) {
            None => 0,
            Some(piece) => {
                let color = match piece.color() {
                    Color::White => 0,
                    Color::Black => 6,
                };
                let kind = match piece.kind() {
                    PieceKind::Pawn => 1,
                    PieceKind::Knight => 2,
                    PieceKind::Bishop => 3,
                    PieceKind::Rook => 4,
                    PieceKind::Queen => 5,
                    PieceKind::King => 6,
                };
                color + kind
            }
        };
        digest.update([code]);
    }
    digest.update([match board.side_to_move() {
        Color::White => 0,
        Color::Black => 1,
    }]);
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
    MoveHash::from_bytes(digest.finalize().into())
}

pub(super) fn calculate_hash(previous: MoveHash, ply: Ply, chess_move: ChessMove) -> MoveHash {
    let mut digest = Sha256::new();
    digest.update(HASH_DOMAIN);
    digest.update(previous.as_bytes());
    digest.update(ply.value().to_be_bytes());
    digest.update([
        chess_move.from().index().value(),
        chess_move.to().index().value(),
        chess_move.promotion_code(),
    ]);
    MoveHash::from_bytes(digest.finalize().into())
}
