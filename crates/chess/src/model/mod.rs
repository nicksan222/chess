//! Foundational, notation-independent chess values.

mod board;
mod chess_move;
mod color;
mod piece;
mod square;
mod square_set;

pub use board::{
    Board, BoardPieces, CastlingRights, FullmoveNumber, HalfmoveClock, InvalidFullmoveNumber,
};
pub use chess_move::{ChessMove, InvalidPromotion, ParseMoveError};
pub use color::Color;
pub use piece::{Piece, PieceKind};
pub use square::{
    AllSquares, BoardDirection, BoardEdge, File, FileOffset, InvalidSquare, ParseSquareError, Rank,
    RankOffset, Square, SquareIndex, SquareOffset, SquareRay,
};
pub use square_set::{SquareCount, SquareSet, Squares as SquareSetSquares};
