//! Complete position conversion for computer search.
//!
//! Rebuilds the search-engine board from a restricted player view without
//! touching authoritative game state; en-passant targets are reconstructed
//! through the engine evaluation API because the dependency exposes no
//! direct setter.

use crate::{
    Color, FileOffset, Piece, PieceKind, RankOffset, Square, SquareOffset, player::PlayerView,
};
use embedded_chess_engine::{Board as SearchBoard, BoardBuilder, Evaluate, Move as SearchMove};

use super::model::{to_position, to_search_color, to_search_piece};
use crate::ComputerError;

/// Converts a restricted player view into a search-engine board.
///
/// Reads only the capabilities exposed for polling (pieces, castling
/// rights, en-passant target, side to move) and never mutates the game.
/// The returned board feeds the synchronous computer search; its result is
/// validated against the view's legal moves before it is ever played.
///
/// # Errors
///
/// Returns [`ComputerError::InconsistentEnPassant`] when the view's
/// en-passant target does not describe a valid double pawn push.
pub(in crate::player::computer) fn to_search_board(
    view: PlayerView<'_>,
) -> Result<SearchBoard, ComputerError> {
    let Some(target) = view.en_passant_target() else {
        return Ok(search_board_builder(view, None)
            .build()
            .set_turn(to_search_color(view.side_to_move())));
    };

    // The dependency exposes no en-passant setter. Reconstruct the position
    // before the double push and apply that move through its evaluation API.
    let mover = view.side_to_move().opposite();
    let push = RankOffset::pawn_push(mover);
    let destination = target
        .offset(SquareOffset::new(FileOffset::ZERO, push))
        .ok_or(ComputerError::InconsistentEnPassant)?;
    let origin = target
        .offset(SquareOffset::new(FileOffset::ZERO, push.reversed()))
        .ok_or(ComputerError::InconsistentEnPassant)?;
    if view.piece_at(origin).is_some()
        || !view
            .piece_at(destination)
            .is_some_and(|piece| piece.color() == mover && piece.kind() == PieceKind::Pawn)
    {
        return Err(ComputerError::InconsistentEnPassant);
    }

    let predecessor = search_board_builder(view, Some(destination))
        .piece(to_search_piece(Piece::new(mover, PieceKind::Pawn, origin)))
        .build()
        .set_turn(to_search_color(mover));
    Ok(predecessor.apply_eval_move(SearchMove::Piece(
        to_position(origin),
        to_position(destination),
    )))
}

fn search_board_builder(view: PlayerView<'_>, omitted: Option<Square>) -> BoardBuilder {
    let mut builder = BoardBuilder::default();
    for piece in view
        .pieces()
        .filter(|piece| Some(piece.square()) != omitted)
    {
        builder = builder.piece(to_search_piece(piece));
    }

    let rights = view.castling_rights();
    for color in Color::ALL {
        let search_color = to_search_color(color);
        if rights.kingside(color) {
            builder = builder.enable_kingside_castle(search_color);
        }
        if rights.queenside(color) {
            builder = builder.enable_queenside_castle(search_color);
        }
    }
    builder
}
