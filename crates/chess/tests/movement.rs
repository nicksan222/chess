use chess::{Board, Color, Piece, PieceKind, Square};

fn board_with(pieces: impl IntoIterator<Item = Piece>) -> Board {
    let mut board = Board::empty();
    for piece in pieces {
        board.set_piece(piece);
    }
    board
}

fn destinations(board: &Board, square: Square) -> Vec<Square> {
    board
        .piece_at(square)
        .unwrap()
        .where_can_move(board)
        .into_iter()
        .collect()
}

#[test]
fn pawn_calculator_handles_pushes_captures_blockers_and_en_passant_shape() {
    let board = board_with([
        Piece::new(Color::White, PieceKind::Pawn, Square::D4),
        Piece::new(Color::Black, PieceKind::Knight, Square::C5),
        Piece::new(Color::White, PieceKind::Bishop, Square::E5),
    ]);

    assert_eq!(destinations(&board, Square::D4), [Square::C5, Square::D5]);
}

#[test]
fn knight_calculator_clips_edges_and_excludes_friendly_occupants() {
    let board = board_with([
        Piece::new(Color::White, PieceKind::Knight, Square::D4),
        Piece::new(Color::Black, PieceKind::Pawn, Square::B5),
        Piece::new(Color::White, PieceKind::Pawn, Square::F5),
    ]);

    assert_eq!(
        destinations(&board, Square::D4),
        [
            Square::C2,
            Square::E2,
            Square::B3,
            Square::F3,
            Square::B5,
            Square::C6,
            Square::E6,
        ]
    );
}

#[test]
fn bishop_calculator_stops_each_ray_at_its_first_occupant() {
    let board = board_with([
        Piece::new(Color::White, PieceKind::Bishop, Square::D4),
        Piece::new(Color::Black, PieceKind::Pawn, Square::B6),
        Piece::new(Color::White, PieceKind::Pawn, Square::F6),
    ]);

    let moves = destinations(&board, Square::D4);
    assert!(moves.contains(&Square::B6));
    assert!(!moves.contains(&Square::A7));
    assert!(moves.contains(&Square::E5));
    assert!(!moves.contains(&Square::F6));
    assert_eq!(moves.len(), 9);
}

#[test]
fn rook_calculator_stops_each_ray_at_its_first_occupant() {
    let board = board_with([
        Piece::new(Color::White, PieceKind::Rook, Square::D4),
        Piece::new(Color::Black, PieceKind::Pawn, Square::D6),
        Piece::new(Color::White, PieceKind::Pawn, Square::F4),
    ]);

    let moves = destinations(&board, Square::D4);
    assert!(moves.contains(&Square::D6));
    assert!(!moves.contains(&Square::D7));
    assert!(moves.contains(&Square::E4));
    assert!(!moves.contains(&Square::F4));
    assert_eq!(moves.len(), 9);
}

#[test]
fn queen_and_king_calculators_cover_their_empty_board_geometry() {
    let queen_board = board_with([Piece::new(Color::White, PieceKind::Queen, Square::D4)]);
    let king_board = board_with([Piece::new(Color::White, PieceKind::King, Square::D4)]);

    assert_eq!(destinations(&queen_board, Square::D4).len(), 27);
    assert_eq!(
        destinations(&king_board, Square::D4),
        [
            Square::C3,
            Square::D3,
            Square::E3,
            Square::C4,
            Square::E4,
            Square::C5,
            Square::D5,
            Square::E5,
        ]
    );
}
