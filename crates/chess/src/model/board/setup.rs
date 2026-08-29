use crate::{Color, Piece, PieceKind, Square};

pub(super) const fn initial_pieces() -> [Option<Piece>; Square::COUNT] {
    let mut pieces = [None; Square::COUNT];
    let back_rank = [
        PieceKind::Rook,
        PieceKind::Knight,
        PieceKind::Bishop,
        PieceKind::Queen,
        PieceKind::King,
        PieceKind::Bishop,
        PieceKind::Knight,
        PieceKind::Rook,
    ];
    let mut file = 0_u8;
    while file < 8 {
        let white_back = Square::from_raw_index_unchecked(file);
        let white_pawn = Square::from_raw_index_unchecked(8 + file);
        let black_pawn = Square::from_raw_index_unchecked(48 + file);
        let black_back = Square::from_raw_index_unchecked(56 + file);
        pieces[white_back.index().value() as usize] = Some(Piece::new(
            Color::White,
            back_rank[file as usize],
            white_back,
        ));
        pieces[white_pawn.index().value() as usize] =
            Some(Piece::new(Color::White, PieceKind::Pawn, white_pawn));
        pieces[black_pawn.index().value() as usize] =
            Some(Piece::new(Color::Black, PieceKind::Pawn, black_pawn));
        pieces[black_back.index().value() as usize] = Some(Piece::new(
            Color::Black,
            back_rank[file as usize],
            black_back,
        ));
        file += 1;
    }
    pieces
}
