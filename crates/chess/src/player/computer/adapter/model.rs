//! Primitive domain-value conversion.
//!
//! Total, side-effect-free mappings between domain values and search-engine
//! primitives. These helpers never touch game state; out-of-range engine
//! positions surface as `None` so callers report
//! [`ComputerError::InvalidSquare`](crate::ComputerError::InvalidSquare).

use crate::{Color, Piece, PieceKind, Square, SquareIndex};
use embedded_chess_engine::{Color as SearchColor, Piece as SearchPiece, Position};

/// Maps a domain color onto its search-engine counterpart.
///
/// Total conversion used when building the synchronous search position.
pub(super) const fn to_search_color(color: Color) -> SearchColor {
    match color {
        Color::White => SearchColor::White,
        Color::Black => SearchColor::Black,
    }
}

/// Maps a domain piece onto its search-engine counterpart.
///
/// Total conversion used when rebuilding the polled position for search.
pub(super) fn to_search_piece(piece: Piece) -> SearchPiece {
    let color = to_search_color(piece.color());
    let position = to_position(piece.square());
    match piece.kind() {
        PieceKind::Pawn => SearchPiece::Pawn(color, position),
        PieceKind::Knight => SearchPiece::Knight(color, position),
        PieceKind::Bishop => SearchPiece::Bishop(color, position),
        PieceKind::Rook => SearchPiece::Rook(color, position),
        PieceKind::Queen => SearchPiece::Queen(color, position),
        PieceKind::King => SearchPiece::King(color, position),
    }
}

/// Maps a domain square onto its search-engine position.
///
/// Total conversion; every domain square has a search-engine position.
pub(super) fn to_position(square: Square) -> Position {
    Position::new(
        i32::from(square.index().value() / 8),
        i32::from(square.index().value() % 8),
    )
}

/// Maps a search-engine position onto a domain square, if in range.
///
/// Returns `None` for out-of-range rows, columns, or indices so the
/// computer poll can report
/// [`InvalidSquare`](crate::ComputerError::InvalidSquare) instead of
/// playing an unrepresentable move.
pub(super) fn from_position(position: Position) -> Option<Square> {
    let rank = u8::try_from(position.get_row()).ok()?;
    let file = u8::try_from(position.get_col()).ok()?;
    let index = SquareIndex::new(rank.checked_mul(8)?.checked_add(file)?).ok()?;
    Some(Square::from_index(index))
}
