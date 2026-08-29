use chess::{
    Board, CastlingRights, Color, FullmoveNumber, HalfmoveClock, Piece, PieceKind, Square,
    SquareSet,
};

#[test]
fn initial_board_has_self_locating_pieces_and_standard_state() {
    const BOARD: Board = Board::INITIAL;
    let white_pawns: SquareSet = [
        Square::A2,
        Square::B2,
        Square::C2,
        Square::D2,
        Square::E2,
        Square::F2,
        Square::G2,
        Square::H2,
    ]
    .into_iter()
    .collect();

    assert_eq!(BOARD.occupied().len().value(), 32);
    assert_eq!(BOARD.occupied_by(Color::White).len().value(), 16);
    assert_eq!(BOARD.occupied_by(Color::Black).len().value(), 16);
    assert_eq!(
        BOARD.occupied_by_kind(Color::White, PieceKind::Pawn),
        white_pawns
    );
    assert_eq!(
        BOARD.piece_at(Square::E1),
        Some(Piece::new(Color::White, PieceKind::King, Square::E1))
    );
    assert_eq!(
        BOARD.piece_at(Square::D8),
        Some(Piece::new(Color::Black, PieceKind::Queen, Square::D8))
    );
    for piece in BOARD.iter() {
        assert_eq!(BOARD.piece_at(piece.square()), Some(piece));
    }
    assert_eq!(BOARD.side_to_move(), Color::White);
    assert_eq!(BOARD.castling_rights(), CastlingRights::ALL);
    assert_eq!(BOARD.en_passant_target(), None);
    assert_eq!(BOARD.halfmove_clock(), HalfmoveClock::ZERO);
    assert_eq!(BOARD.fullmove_number(), FullmoveNumber::ONE);
}

#[test]
fn setting_a_piece_uses_its_square_and_replaces_the_occupant() {
    let mut board = Board::empty();
    let white_rook = Piece::new(Color::White, PieceKind::Rook, Square::E4);
    let black_queen = Piece::new(Color::Black, PieceKind::Queen, Square::E4);

    assert_eq!(board.set_piece(white_rook), None);
    assert_eq!(board.set_piece(black_queen), Some(white_rook));
    assert_eq!(board.piece_at(Square::E4), Some(black_queen));
    assert!(
        !board
            .occupied_by_kind(Color::White, PieceKind::Rook)
            .contains(Square::E4)
    );
    assert!(
        board
            .occupied_by_kind(Color::Black, PieceKind::Queen)
            .contains(Square::E4)
    );
    assert_eq!(board.occupied().len().value(), 1);
    assert_eq!(board.remove_piece(Square::E4), Some(black_queen));
    assert!(board.occupied().is_empty());
}

#[test]
fn piece_iteration_is_ordered_exact_sized_and_double_ended() {
    let mut board = Board::empty();
    let rook = Piece::new(Color::White, PieceKind::Rook, Square::A1);
    let knight = Piece::new(Color::Black, PieceKind::Knight, Square::E4);
    let king = Piece::new(Color::White, PieceKind::King, Square::H8);
    board.set_piece(rook);
    board.set_piece(knight);
    board.set_piece(king);

    assert_eq!(
        (&board).into_iter().collect::<Vec<_>>(),
        [rook, knight, king]
    );

    let mut pieces = board.pieces();
    assert_eq!(pieces.len(), 3);
    assert_eq!(pieces.next(), Some(rook));
    assert_eq!(pieces.next_back(), Some(king));
    assert_eq!(pieces.next(), Some(knight));
    assert_eq!(pieces.next(), None);
}

#[test]
fn board_state_uses_domain_values() {
    let mut board = Board::INITIAL;
    let occupied = board.occupied();
    let mut rights = board.castling_rights();
    rights.clear(Color::White);
    rights.set_queenside(Color::Black, false);

    board.set_side_to_move(Color::Black);
    board.set_castling_rights(rights);
    board.set_en_passant_target(Some(Square::E3));
    board.set_halfmove_clock(HalfmoveClock::new(12));
    board.set_fullmove_number(FullmoveNumber::new(23).unwrap());

    assert_eq!(board.occupied(), occupied);
    assert_eq!(board.side_to_move(), Color::Black);
    assert!(!board.castling_rights().kingside(Color::White));
    assert!(!board.castling_rights().queenside(Color::White));
    assert!(board.castling_rights().kingside(Color::Black));
    assert!(!board.castling_rights().queenside(Color::Black));
    assert_eq!(board.en_passant_target(), Some(Square::E3));
    assert_eq!(board.halfmove_clock(), HalfmoveClock::new(12));
    assert_eq!(board.fullmove_number(), FullmoveNumber::new(23).unwrap());
}

#[test]
fn fullmove_numbers_are_one_based() {
    let error = FullmoveNumber::new(0).expect_err("zero is not a fullmove number");

    assert_eq!(error.to_string(), "fullmove number must be at least one");
}
