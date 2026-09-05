//! Restricted position access for move sources.

use crate::{BoardPieces, CastlingRights, ChessMove, Color, Game, Piece, Square};

/// The position information available to the player whose turn is being polled.
///
/// This capability intentionally exposes neither [`Game`] nor [`crate::Board`].
/// A move source can inspect the position and enumerate legal moves, but cannot
/// mutate authoritative state, append history, resolve invalid events, or end
/// the game.
#[derive(Clone, Copy)]
pub(crate) struct PlayerView<'a> {
    game: &'a Game,
}

impl<'a> PlayerView<'a> {
    /// Borrows the authoritative game as a restricted polling snapshot.
    ///
    /// Called by [`GameSession`](crate::GameSession) with the side to move;
    /// the resulting view is handed to exactly one non-blocking player poll.
    pub(crate) const fn new(game: &'a Game) -> Self {
        Self { game }
    }

    /// Returns the color this player is being asked to move.
    ///
    /// Identifies which [`GameSession`](crate::GameSession) side is being
    /// polled; only that side's player is consulted on this turn.
    #[must_use]
    pub(crate) const fn side_to_move(self) -> Color {
        self.game.side_to_move()
    }

    /// Returns the piece on `square`, if occupied.
    ///
    /// Read-only inspection for move sources; it reveals position state
    /// without exposing mutation, history, or game control.
    #[must_use]
    pub(crate) const fn piece_at(self, square: Square) -> Option<Piece> {
        self.game.piece_at(square)
    }

    /// Iterates over every piece in board order.
    ///
    /// Lets the synchronous computer search rebuild its board snapshot from
    /// read-only state; it confers no ability to move pieces or edit the
    /// [`Game`](crate::Game).
    pub(crate) fn pieces(self) -> BoardPieces<'a> {
        self.game.pieces()
    }

    /// Iterates over every legal move in the current position.
    ///
    /// Move sources validate candidates against this enumeration: the
    /// computer poll prefers the matching legal promotion and checks its
    /// result before answering, while the session revalidates consumed
    /// moves through authoritative play.
    pub(crate) fn legal_moves(self) -> impl Iterator<Item = ChessMove> + 'a {
        self.game.legal_moves()
    }

    /// Returns the castling rights retained by the current position.
    ///
    /// Read-only search input used to rebuild the computer board snapshot;
    /// it cannot grant or consume rights on the authoritative game.
    #[must_use]
    pub(crate) const fn castling_rights(self) -> CastlingRights {
        self.game.board().castling_rights()
    }

    /// Returns the current en-passant target, if any.
    ///
    /// Read-only search input; inconsistent targets surface as
    /// [`InconsistentEnPassant`](crate::ComputerError::InconsistentEnPassant)
    /// during computer polling rather than mutating game state.
    #[must_use]
    pub(crate) const fn en_passant_target(self) -> Option<Square> {
        self.game.board().en_passant_target()
    }
}
