//! Explicit relocations that intentionally bypass chess rules.

use core::fmt;

use crate::{Board, Piece, Square};

/// The result of an explicit board relocation that bypassed chess rules.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct ForcedMove {
    moved: Piece,
    captured: Option<Piece>,
}

impl ForcedMove {
    /// Returns the relocated, self-locating piece.
    #[must_use]
    pub const fn moved(self) -> Piece {
        self.moved
    }

    /// Returns the piece displaced from the destination, if any.
    #[must_use]
    pub const fn captured(self) -> Option<Piece> {
        self.captured
    }
}

/// A forced relocation whose origin contains no piece.
#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub struct ForceMoveError {
    origin: Square,
}

impl ForceMoveError {
    /// Returns the empty origin square.
    #[must_use]
    pub const fn origin(self) -> Square {
        self.origin
    }
}

impl fmt::Display for ForceMoveError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            formatter,
            "cannot force a move from empty square {}",
            self.origin
        )
    }
}

impl_error!(ForceMoveError);

impl Board {
    /// Relocates a piece without checking movement rules or changing game
    /// metadata.
    ///
    /// This is intended for board setup and physical-board reconciliation.
    /// It does not change the side to move, clocks, castling rights, en-passant
    /// state, or hash-linked game history. Normal play must use legal game
    /// movement instead.
    pub fn force_move(
        &mut self,
        origin: Square,
        destination: Square,
    ) -> Result<ForcedMove, ForceMoveError> {
        let piece = self.remove_piece(origin).ok_or(ForceMoveError { origin })?;
        let captured = self.remove_piece(destination);
        let moved = piece.at(destination);
        self.set_piece(moved);
        Ok(ForcedMove { moved, captured })
    }
}

impl Square {
    /// Forces the piece on this square to `destination` in `board`.
    ///
    /// See [`Board::force_move`] for the deliberately limited semantics.
    pub fn force_move_to(
        self,
        destination: Square,
        board: &mut Board,
    ) -> Result<ForcedMove, ForceMoveError> {
        board.force_move(self, destination)
    }
}
