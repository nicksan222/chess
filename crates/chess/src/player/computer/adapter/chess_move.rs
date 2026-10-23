//! Search-move conversion and canonical promotion handling.
//!
//! Maps engine moves back onto domain [`ChessMove`] values, preferring the
//! matching legal promotion so a queen-only engine result still selects a
//! legal domain move. A `Resign` result maps to `None` so the synchronous
//! computer poll can yield pending or report resignation.

use crate::{
    ChessMove, ComputerError, PieceKind, Rank,
    model::{Castle, CastleSide},
    player::PlayerView,
};
use embedded_chess_engine::Move as SearchMove;

use super::model::from_position;

/// Converts a search-engine move into a domain move, if the engine moved.
///
/// Castling results map onto the side-to-move king squares, piece moves map
/// through square conversion, and promotion results prefer the matching
/// legal promotion from the restricted view. The outcome is validated
/// against the view's legal moves by the synchronous computer poll before
/// it reaches the session.
///
/// # Errors
///
/// Returns [`ComputerError::InvalidSquare`] when the engine returns a
/// square outside the domain board.
pub(in crate::player::computer) fn from_search_move(
    search_move: SearchMove,
    view: PlayerView<'_>,
) -> Result<Option<ChessMove>, ComputerError> {
    let (from, to) = match search_move {
        SearchMove::KingSideCastle => {
            Castle::new(view.side_to_move(), CastleSide::Kingside).king_move()
        }
        SearchMove::QueenSideCastle => {
            Castle::new(view.side_to_move(), CastleSide::Queenside).king_move()
        }
        SearchMove::Piece(from, to) => (
            from_position(from).ok_or(ComputerError::InvalidSquare)?,
            from_position(to).ok_or(ComputerError::InvalidSquare)?,
        ),
        SearchMove::Resign => return Ok(None),
    };

    let promotes = view
        .piece_at(from)
        .is_some_and(|piece| piece.kind() == PieceKind::Pawn)
        && matches!(to.rank(), Rank::One | Rank::Eight);
    if !promotes {
        return Ok(Some(ChessMove::new(from, to)));
    }

    // The search engine has no promotion-kind concept and always promotes to a
    // queen. Select the matching legal promotion instead of constructing one
    // blindly: prefer queen, otherwise take whatever underpromotion the domain
    // allows for this from/to pair. Falling through to a queen construction
    // lets the caller report `IllegalMove` if no promotion matches.
    let mut fallback: Option<ChessMove> = None;
    for legal in view.legal_moves() {
        if legal.from() != from || legal.to() != to {
            continue;
        }
        match legal.promotion_kind() {
            Some(PieceKind::Queen) => return Ok(Some(legal)),
            Some(_) if fallback.is_none() => fallback = Some(legal),
            _ => {}
        }
    }
    if let Some(underpromotion) = fallback {
        return Ok(Some(underpromotion));
    }
    Ok(Some(
        ChessMove::promotion(from, to, PieceKind::Queen)
            .expect("queen is always a valid promotion kind"),
    ))
}
