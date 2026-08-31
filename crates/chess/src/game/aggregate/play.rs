//! Local move application and invalid-move recording.

use crate::{
    ChessMove, HistoryEvent, HistoryStep, InvalidState, MoveError, Piece, PieceKind, Square,
};

use super::Game;

impl Game {
    /// Applies and records a locally initiated move.
    pub fn play(&mut self, chess_move: ChessMove) -> Result<HistoryStep, MoveError> {
        if let Some(error) = self.blocking_move_error() {
            if error == MoveError::PendingInvalid {
                self.record_invalid(InvalidState::PendingInvalid);
            }
            return Err(error);
        }

        let canonical = match self.board.make_move(chess_move) {
            Ok(canonical) => canonical,
            Err(error) => {
                self.record_invalid(InvalidState::Move(error));
                return Err(error);
            }
        };
        let step = self
            .history
            .push(HistoryEvent::Move(canonical))
            .expect("an active game accepts a valid move event");
        self.finalize_if_terminal();
        Ok(step)
    }

    pub(crate) fn move_piece(
        &mut self,
        piece: Piece,
        destination: Square,
        promotion: Option<PieceKind>,
    ) -> Result<HistoryStep, MoveError> {
        if self.board.piece_at(piece.square()) != Some(piece) {
            let error = MoveError::StalePiece;
            self.record_invalid(InvalidState::Move(error));
            return Err(error);
        }
        let chess_move = match promotion {
            Some(kind) => {
                ChessMove::promotion(piece.square(), destination, kind).map_err(|_| {
                    let error = MoveError::InvalidPromotion;
                    self.record_invalid(InvalidState::Move(error));
                    error
                })?
            }
            None => ChessMove::new(piece.square(), destination),
        };
        self.play(chess_move)
    }
}
