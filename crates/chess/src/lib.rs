//! A `no_std`, integration-neutral chess engine.
//!
//! The crate separates immutable domain values ([`Square`], [`Piece`],
//! [`ChessMove`], and [`Board`]) from the [`Game`] aggregate. A game retains an
//! initial board, a derived current-board cache, and one authoritative
//! [`GameHistory`].
//!
//! # Authoritative events
//!
//! Every accepted move, unresolved invalid operation, and terminal result is a
//! [`HistoryEvent`] inside a SHA-256-linked [`HistoryStep`]. Invalid events
//! block valid play and are resolved newest-first with
//! [`Game::resolve_latest_invalid`]. A [`FinalState`] permanently seals the
//! timeline. [`Game::verify`] replays move events and confirms that history
//! still reproduces the board cache.
//!
//! # Example
//!
//! ```
//! use chess::{ChessMove, Game, HistoryEvent, Square};
//!
//! let mut game = Game::new();
//! let step = game.play(ChessMove::new(Square::E2, Square::E4))?;
//! assert!(matches!(step.event(), HistoryEvent::Move(_)));
//! assert_eq!(game.rebuild_board()?, *game.board());
//! game.verify()?;
//! # Ok::<(), Box<dyn core::error::Error>>(())
//! ```
//!
//! Hardware observation, persistence, transport, authentication, user
//! interfaces, and logging remain outside this crate.

#![no_std]
#![forbid(unsafe_code)]
#![warn(missing_docs)]

#[macro_use]
mod macros;

mod game;
mod model;

pub use game::{
    DrawClaim, DrawClaimError, DrawClaims, DrawReason, FinalState, ForceMoveError, ForcedMove,
    Game, GameHistory, GameHistoryIter, GameStatus, GameSyncError, GameVerificationError,
    HistoryCount, HistoryError, HistoryEvent, HistoryEventKind, HistoryHash, HistoryStep,
    InvalidPly, InvalidState, MoveError, Ply,
};
pub use model::{
    AllSquares, Board, BoardDirection, BoardEdge, BoardPieces, CastlingRights, ChessMove, Color,
    File, FileOffset, FullmoveNumber, HalfmoveClock, InvalidFullmoveNumber, InvalidPromotion,
    InvalidSquare, ParseMoveError, ParseSquareError, Piece, PieceKind, Rank, RankOffset, Square,
    SquareCount, SquareIndex, SquareOffset, SquareRay, SquareSet, SquareSetSquares,
};
