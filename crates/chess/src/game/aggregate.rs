use crate::{Board, ChessMove, Piece, PieceKind, Square};

use super::{GameSyncError, MoveError, MoveHistory, MoveStep};

/// A playable board coupled to its hash-linked move history.
#[derive(Clone, Debug, PartialEq, Eq)]
pub struct Game {
    board: Board,
    history: MoveHistory,
}

impl Game {
    /// Creates a game in the standard initial board.
    #[must_use]
    pub fn new() -> Self {
        Self::from_board(Board::INITIAL)
    }

    /// Creates a game from a board with an empty history anchored to it.
    #[must_use]
    pub fn from_board(board: Board) -> Self {
        Self {
            history: MoveHistory::for_board(&board),
            board,
        }
    }

    /// Returns the current board.
    #[must_use]
    pub const fn board(&self) -> &Board {
        &self.board
    }

    /// Returns the piece currently occupying `square`.
    #[must_use]
    pub const fn piece_at(&self, square: Square) -> Option<Piece> {
        self.board.piece_at(square)
    }

    /// Returns the immutable, hash-linked move history.
    #[must_use]
    pub const fn history(&self) -> &MoveHistory {
        &self.history
    }

    /// Applies and records a locally initiated move.
    pub fn play(&mut self, chess_move: ChessMove) -> Result<MoveStep, MoveError> {
        let canonical = self.board.make_move(chess_move)?;
        Ok(self.history.push(canonical))
    }

    /// Verifies, applies, and records a move step received from a peer.
    ///
    /// The hash link is checked against every previous local move before the
    /// newest move is applied. Neither board nor history changes on error.
    pub fn accept(&mut self, step: MoveStep) -> Result<(), GameSyncError> {
        self.history
            .validate_next(step)
            .map_err(GameSyncError::History)?;
        let mut next = self.board;
        let canonical = next
            .make_move(step.chess_move())
            .map_err(GameSyncError::Move)?;
        if canonical != step.chess_move() {
            return Err(GameSyncError::Move(MoveError::NonCanonicalPromotion));
        }
        self.board = next;
        self.history.append_validated(step);
        Ok(())
    }

    pub(crate) fn move_piece(
        &mut self,
        piece: Piece,
        destination: Square,
        promotion: Option<PieceKind>,
    ) -> Result<MoveStep, MoveError> {
        if self.board.piece_at(piece.square()) != Some(piece) {
            return Err(MoveError::StalePiece);
        }
        let chess_move = match promotion {
            Some(kind) => ChessMove::promotion(piece.square(), destination, kind)
                .map_err(|_| MoveError::InvalidPromotion)?,
            None => ChessMove::new(piece.square(), destination),
        };
        self.play(chess_move)
    }
}

impl Default for Game {
    fn default() -> Self {
        Self::new()
    }
}
