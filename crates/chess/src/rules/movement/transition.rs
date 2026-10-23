//! Unchecked board transitions and rule-state updates.

use crate::{
    Board, Color, FileOffset, HalfmoveClock, Piece, PieceKind, Rank, RankOffset, Square,
    SquareOffset, model::Castle,
};

impl Board {
    /// Applies `piece` to `destination` without legality checks.
    ///
    /// Handles the canonical transition: normal and en-passant captures,
    /// pawn promotion (defaulting to queen when it reaches the back rank),
    /// castling rook relocation with rights updates, rook-origin and capture
    /// rights revocation, halfmove/fullmove clocks, en-passant target, and
    /// side-to-move flip. Callers must validate via
    /// [`Board::legal_destinations`](crate::Board::legal_destinations) first;
    /// [`Board::make_move`](crate::Board::make_move) is the checked entry.
    pub(super) fn apply_unchecked(
        &mut self,
        piece: Piece,
        destination: Square,
        promotion: Option<PieceKind>,
    ) {
        let captured = self.take_captured_piece(piece, destination);
        self.place_moved_piece(piece, destination, promotion);
        self.relocate_castling_rook(piece, destination);
        self.revoke_castling_rights(piece, captured);
        self.finish_move(piece, destination, captured);
    }

    /// Removes and returns the piece captured by `piece` moving to `destination`.
    ///
    /// Covers both a normal capture and an en-passant capture, where the
    /// victim stands behind the destination square.
    fn take_captured_piece(&mut self, piece: Piece, destination: Square) -> Option<Piece> {
        let captured = self.remove_piece(destination);
        if captured.is_some()
            || piece.kind() != PieceKind::Pawn
            || self.en_passant_target() != Some(destination)
        {
            return captured;
        }
        let behind = SquareOffset::new(
            FileOffset::ZERO,
            RankOffset::pawn_push(piece.color()).reversed(),
        );
        destination
            .offset(behind)
            .and_then(|square| self.remove_piece(square))
    }

    /// Moves `piece` to `destination`, promoting when it reaches the back rank.
    fn place_moved_piece(
        &mut self,
        piece: Piece,
        destination: Square,
        promotion: Option<PieceKind>,
    ) {
        self.remove_piece(piece.square());
        let mut moved = piece.at(destination);
        if let Some(kind) = promotion.or_else(|| {
            (piece.kind() == PieceKind::Pawn && is_back_rank(destination, piece.color()))
                .then_some(PieceKind::Queen)
        }) {
            moved = moved.promoted(kind);
        }
        self.set_piece(moved);
    }

    /// Moves the rook alongside a castling king move.
    fn relocate_castling_rook(&mut self, piece: Piece, destination: Square) {
        if piece.kind() != PieceKind::King {
            return;
        }
        if let Some(castle) = Castle::from_king_move(piece.square(), destination) {
            let (from, to) = castle.rook_move();
            if let Some(rook) = self.remove_piece(from) {
                self.set_piece(rook.at(to));
            }
        }
    }

    /// Revokes rights lost by a king move, a rook leaving or a rook captured.
    fn revoke_castling_rights(&mut self, piece: Piece, captured: Option<Piece>) {
        let mut rights = self.castling_rights();
        if piece.kind() == PieceKind::King {
            rights.clear(piece.color());
        }
        for rook in [Some(piece), captured].into_iter().flatten() {
            if rook.kind() != PieceKind::Rook {
                continue;
            }
            if let Some(castle) = Castle::from_rook_origin(rook.color(), rook.square()) {
                rights.revoke(castle.color(), castle.side());
            }
        }
        self.set_castling_rights(rights);
    }

    /// Updates clocks, the en-passant target and the side to move.
    fn finish_move(&mut self, moved: Piece, destination: Square, captured: Option<Piece>) {
        let mut halfmove_clock = self.halfmove_clock();
        if moved.kind() == PieceKind::Pawn || captured.is_some() {
            halfmove_clock = HalfmoveClock::ZERO;
        } else {
            halfmove_clock.increment();
        }
        self.set_halfmove_clock(halfmove_clock);

        let en_passant_target = is_initial_double_pawn_push(moved, destination)
            .then(|| {
                moved.square().offset(SquareOffset::new(
                    FileOffset::ZERO,
                    RankOffset::pawn_push(moved.color()),
                ))
            })
            .flatten();
        self.set_en_passant_target(en_passant_target);

        if moved.color() == Color::Black {
            let mut fullmove_number = self.fullmove_number();
            fullmove_number.increment();
            self.set_fullmove_number(fullmove_number);
        }
        self.set_side_to_move(moved.color().opposite());
    }
}

/// Returns whether `square` is the promotion back rank for `color`.
///
/// White promotes on rank eight and Black on rank one. Used to expand
/// promotion [`crate::ChessMove`]s and to default unchecked pawn pushes to
/// queen.
pub(super) fn is_back_rank(square: Square, color: Color) -> bool {
    square.rank()
        == match color {
            Color::White => Rank::Eight,
            Color::Black => Rank::One,
        }
}

fn is_initial_double_pawn_push(piece: Piece, destination: Square) -> bool {
    piece.kind() == PieceKind::Pawn
        && matches!(
            (piece.color(), piece.square().rank(), destination.rank()),
            (Color::White, Rank::Two, Rank::Four) | (Color::Black, Rank::Seven, Rank::Five)
        )
}
