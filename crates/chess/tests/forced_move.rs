use chess::{
    Board, CastlingRights, Color, FullmoveNumber, HalfmoveClock, Piece, PieceKind, Square,
};

#[test]
fn square_can_force_a_relocation_without_chess_validation() {
    let mut board = Board::INITIAL;
    let side = board.side_to_move();
    let rights = board.castling_rights();
    let halfmoves = board.halfmove_clock();
    let fullmove = board.fullmove_number();

    let forced = Square::E2.force_move_to(Square::E7, &mut board).unwrap();

    assert_eq!(forced.moved().square(), Square::E7);
    assert_eq!(forced.moved().color(), Color::White);
    assert_eq!(forced.moved().kind(), PieceKind::Pawn);
    assert_eq!(
        forced.captured(),
        Some(Piece::new(Color::Black, PieceKind::Pawn, Square::E7))
    );
    assert_eq!(board.piece_at(Square::E2), None);
    assert_eq!(board.piece_at(Square::E7), Some(forced.moved()));
    assert_eq!(board.side_to_move(), side);
    assert_eq!(board.castling_rights(), rights);
    assert_eq!(board.halfmove_clock(), halfmoves);
    assert_eq!(board.fullmove_number(), fullmove);
}

#[test]
fn board_force_move_reports_an_empty_origin_without_mutation() {
    let mut board = Board::empty();
    board.set_castling_rights(CastlingRights::ALL);
    board.set_halfmove_clock(HalfmoveClock::new(12));
    board.set_fullmove_number(FullmoveNumber::new(7).unwrap());
    let before = board;

    let error = board.force_move(Square::D4, Square::D5).unwrap_err();

    assert_eq!(error.origin(), Square::D4);
    assert_eq!(
        error.to_string(),
        "cannot force a move from empty square d4"
    );
    assert_eq!(board, before);
}

#[test]
fn forced_relocation_to_the_same_square_is_stable() {
    let mut board = Board::empty();
    let king = Piece::new(Color::White, PieceKind::King, Square::E1);
    board.set_piece(king);

    let forced = board.force_move(Square::E1, Square::E1).unwrap();

    assert_eq!(forced.moved(), king);
    assert_eq!(forced.captured(), None);
    assert_eq!(board.piece_at(Square::E1), Some(king));
}
