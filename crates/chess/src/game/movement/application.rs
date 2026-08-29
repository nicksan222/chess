use crate::{Board, Color, Piece, PieceKind, Rank, Square, SquareOffset};

impl Board {
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

        let double_push = piece.kind() == PieceKind::Pawn
            && piece.square().rank().distance(destination.rank()) == RankDistance::Two;
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

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
enum RankDistance {
    Zero,
    One,
    Two,
    Three,
    Four,
    Five,
    Six,
    Seven,
}

trait Distance {
    fn distance(self, other: Self) -> RankDistance;
}

impl Distance for Rank {
    fn distance(self, other: Self) -> RankDistance {
        match (self as u8).abs_diff(other as u8) {
            0 => RankDistance::Zero,
            1 => RankDistance::One,
            2 => RankDistance::Two,
            3 => RankDistance::Three,
            4 => RankDistance::Four,
            5 => RankDistance::Five,
            6 => RankDistance::Six,
            7 => RankDistance::Seven,
            _ => unreachable!("ranks are at most seven squares apart"),
        }
    }
}
