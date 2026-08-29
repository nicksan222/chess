use crate::{Board, ChessMove, PieceKind};

use super::{MoveError, transition::is_back_rank};

impl Board {
    pub(crate) fn make_move(&mut self, chess_move: ChessMove) -> Result<ChessMove, MoveError> {
        let piece = self.piece_at(chess_move.from()).ok_or(MoveError::NoPiece {
            square: chess_move.from(),
        })?;
        if piece.color() != self.side_to_move() {
            return Err(MoveError::WrongSide {
                expected: self.side_to_move(),
                actual: piece.color(),
            });
        }
        if !self.legal_destinations(piece).contains(chess_move.to()) {
            return Err(MoveError::IllegalDestination {
                from: chess_move.from(),
                to: chess_move.to(),
            });
        }

        let reaches_back_rank =
            piece.kind() == PieceKind::Pawn && is_back_rank(chess_move.to(), piece.color());
        let promotion = match (reaches_back_rank, chess_move.promotion_kind()) {
            (true, None) => Some(PieceKind::Queen),
            (
                true,
                Some(
                    kind @ (PieceKind::Knight
                    | PieceKind::Bishop
                    | PieceKind::Rook
                    | PieceKind::Queen),
                ),
            ) => Some(kind),
            (true, Some(PieceKind::Pawn | PieceKind::King)) => {
                return Err(MoveError::InvalidPromotion);
            }
            (false, None) => None,
            (false, Some(_)) => return Err(MoveError::UnexpectedPromotion),
        };
        self.apply_unchecked(piece, chess_move.to(), promotion);
        let canonical = match promotion {
            Some(kind) => ChessMove::promotion(chess_move.from(), chess_move.to(), kind)
                .expect("validated promotion kinds are constructible"),
            None => chess_move,
        };
        Ok(canonical)
    }
}
