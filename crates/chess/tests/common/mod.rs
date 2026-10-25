#![allow(
    dead_code,
    reason = "each test crate uses a different subset of the shared helpers"
)]

pub(crate) mod perft;

use chess::{Board, ChessMove, Game, Piece, Square};

pub(crate) fn board_with(pieces: impl IntoIterator<Item = Piece>) -> Board {
    Board::from_pieces(pieces)
}

pub(crate) fn play(game: &mut Game, from: Square, to: Square) {
    ChessMove::new(from, to).play(game).expect("move is legal");
}
