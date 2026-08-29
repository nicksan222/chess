use crate::{Board, ChessMove, Color, Piece, PieceKind, Rank, Square, SquareOffset};

use super::MoveError;

impl Board {
    pub(crate) fn make_move(&mut self, chess_move: ChessMove) -> Result<ChessMove, MoveError> {
        let piece = self.piece_at(chess_move.from()).ok_or(MoveError::NoPiece {
            square: chess_move.from(),
        })?;
        if piece.color() != self.side_to_move() {
            return Err(MoveError::WrongSide {
                expected: self.side_to_move(),
                actual: piece.color(),
            });
        }
        if !self.destinations(piece).contains(chess_move.to()) {
            return Err(MoveError::IllegalDestination {
                from: chess_move.from(),
                to: chess_move.to(),
            });
        }

        let reaches_back_rank =
            piece.kind() == PieceKind::Pawn && Self::is_back_rank(chess_move.to(), piece.color());
        let promotion = match (reaches_back_rank, chess_move.promotion_kind()) {
            (true, None) => Some(PieceKind::Queen),
            (
                true,
                Some(
                    kind @ (PieceKind::Knight
                    | PieceKind::Bishop
                    | PieceKind::Rook
                    | PieceKind::Queen),
                ),
            ) => Some(kind),
            (true, Some(PieceKind::Pawn | PieceKind::King)) => {
                return Err(MoveError::InvalidPromotion);
            }
            (false, None) => None,
            (false, Some(_)) => return Err(MoveError::UnexpectedPromotion),
        };
        self.apply_unchecked(piece, chess_move.to(), promotion);
        let canonical = match promotion {
            Some(kind) => ChessMove::promotion(chess_move.from(), chess_move.to(), kind)
                .expect("validated promotion kinds are constructible"),
            None => chess_move,
        };
        Ok(canonical)
    }

    pub(super) fn apply_unchecked(
        &mut self,
        piece: Piece,
        destination: Square,
        promotion: Option<PieceKind>,
    ) {
        let mut captured = self.remove_piece(destination);
        if piece.kind() == PieceKind::Pawn
            && self.en_passant_target() == Some(destination)
            && captured.is_none()
        {
            let behind = match piece.color() {
                Color::White => SquareOffset::new(0, -1),
                Color::Black => SquareOffset::new(0, 1),
            };
            captured = destination
                .offset(behind)
                .and_then(|square| self.remove_piece(square));
        }

        self.remove_piece(piece.square());
        let mut moved = piece.at(destination);
        if let Some(kind) = promotion.or_else(|| {
            (piece.kind() == PieceKind::Pawn && Self::is_back_rank(destination, piece.color()))
                .then_some(PieceKind::Queen)
        }) {
            moved = moved.promoted(kind);
        }
        self.set_piece(moved);

        if piece.kind() == PieceKind::King {
            let mut rights = self.castling_rights();
            rights.clear(piece.color());
            self.set_castling_rights(rights);
            let rook_move = match (piece.square(), destination) {
                (Square::E1, Square::G1) => Some((Square::H1, Square::F1)),
                (Square::E1, Square::C1) => Some((Square::A1, Square::D1)),
                (Square::E8, Square::G8) => Some((Square::H8, Square::F8)),
                (Square::E8, Square::C8) => Some((Square::A8, Square::D8)),
                _ => None,
            };
            if let Some((from, to)) = rook_move
                && let Some(rook) = self.remove_piece(from)
            {
                self.set_piece(rook.at(to));
            }
        }
        self.update_rook_right(piece);
        if let Some(captured) = captured {
            self.update_rook_right(captured);
        }

        let double_push = is_initial_double_pawn_push(piece, destination);
        self.finish_move(piece, captured, double_push);
    }

    fn update_rook_right(&mut self, piece: Piece) {
        if piece.kind() != PieceKind::Rook {
            return;
        }
        let mut rights = self.castling_rights();
        match (piece.color(), piece.square()) {
            (Color::White, Square::H1) => rights.set_kingside(Color::White, false),
            (Color::White, Square::A1) => rights.set_queenside(Color::White, false),
            (Color::Black, Square::H8) => rights.set_kingside(Color::Black, false),
            (Color::Black, Square::A8) => rights.set_queenside(Color::Black, false),
            _ => return,
        }
        self.set_castling_rights(rights);
    }
}

fn is_initial_double_pawn_push(piece: Piece, destination: Square) -> bool {
    piece.kind() == PieceKind::Pawn
        && matches!(
            (piece.color(), piece.square().rank(), destination.rank()),
            (Color::White, Rank::Two, Rank::Four) | (Color::Black, Rank::Seven, Rank::Five)
        )
}
