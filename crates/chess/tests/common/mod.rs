#![allow(dead_code)]

pub mod perft;

use chess::{Board, ChessMove, Game, Piece, Square};

pub fn board_with(pieces: impl IntoIterator<Item = Piece>) -> Board {
    Board::from_pieces(pieces)
}

pub fn play(game: &mut Game, from: Square, to: Square) {
    ChessMove::new(from, to).play(game).expect("move is legal");
}
