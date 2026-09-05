use crate::{Board, CastlingRights, Color, Game, Piece, PieceKind, Square, player::PlayerView};
use embedded_chess_engine::{Color as SearchColor, Piece as SearchPiece, Position};

use super::{
    from_search_move,
    model::{from_position, to_position},
    to_search_board,
};
use embedded_chess_engine::Move as SearchMove;

#[test]
fn every_square_round_trips_through_engine_coordinates() {
    for square in Square::all() {
        assert_eq!(from_position(to_position(square)), Some(square));
    }
}

#[test]
fn conversion_preserves_turn_castling_and_en_passant() {
    let mut board = Board::from_pieces([
        Piece::new(Color::White, PieceKind::King, Square::E1),
        Piece::new(Color::White, PieceKind::Rook, Square::A1),
        Piece::new(Color::White, PieceKind::Rook, Square::H1),
        Piece::new(Color::White, PieceKind::Pawn, Square::E4),
        Piece::new(Color::Black, PieceKind::King, Square::E8),
        Piece::new(Color::Black, PieceKind::Rook, Square::A8),
        Piece::new(Color::Black, PieceKind::Rook, Square::H8),
    ]);
    board.set_side_to_move(Color::Black);
    board.set_castling_rights(CastlingRights::ALL);
    board.set_en_passant_target(Some(Square::E3));
    let game = Game::from_board(board);

    let search = to_search_board(PlayerView::new(&game)).unwrap();
    assert_eq!(search.get_turn_color(), SearchColor::Black);
    assert_eq!(search.get_en_passant(), Some(Position::new(2, 4)));
    assert!(search.can_kingside_castle(SearchColor::White));
    assert!(search.can_queenside_castle(SearchColor::White));
    assert!(search.can_kingside_castle(SearchColor::Black));
    assert!(search.can_queenside_castle(SearchColor::Black));
}

#[test]
fn search_pawn_push_to_last_rank_prefers_queen_promotion() {
    let board = Board::from_pieces([
        Piece::new(Color::White, PieceKind::King, Square::H1),
        Piece::new(Color::White, PieceKind::Pawn, Square::E7),
        Piece::new(Color::Black, PieceKind::King, Square::A8),
    ]);
    let game = Game::from_board(board);
    let view = PlayerView::new(&game);
    assert!(
        game.legal_moves()
            .any(|legal| legal.promotion_kind() == Some(PieceKind::Queen))
    );

    let converted = from_search_move(
        SearchMove::Piece(to_position(Square::E7), to_position(Square::E8)),
        view,
    )
    .expect("a pawn push converts")
    .expect("a pawn push is not a resignation");
    assert_eq!(converted.from(), Square::E7);
    assert_eq!(converted.to(), Square::E8);
    assert_eq!(converted.promotion_kind(), Some(PieceKind::Queen));
    assert!(game.legal_moves().any(|legal| legal == converted));
}

#[test]
fn search_resignation_converts_to_no_move() {
    let game = Game::new();
    let converted =
        from_search_move(SearchMove::Resign, PlayerView::new(&game)).expect("resignation converts");
    assert_eq!(converted, None);
}

#[test]
fn search_non_promotion_passes_through_unchanged() {
    let game = Game::new();
    let converted = from_search_move(
        SearchMove::Piece(to_position(Square::E2), to_position(Square::E4)),
        PlayerView::new(&game),
    )
    .expect("a pawn push converts")
    .expect("a pawn push is not a resignation");
    assert_eq!(converted, crate::ChessMove::new(Square::E2, Square::E4));
}

#[test]
fn conversion_preserves_underpromoted_pieces() {
    let mut board = Board::from_pieces([
        Piece::new(Color::White, PieceKind::King, Square::H1),
        Piece::new(Color::White, PieceKind::Knight, Square::A8),
        Piece::new(Color::White, PieceKind::Rook, Square::A1),
        Piece::new(Color::Black, PieceKind::King, Square::H8),
        Piece::new(Color::Black, PieceKind::Queen, Square::D8),
    ]);
    board.set_castling_rights(CastlingRights::NONE);
    let game = Game::from_board(board);

    let search = to_search_board(PlayerView::new(&game)).unwrap();
    assert_eq!(
        search.get_piece(Position::new(7, 0)),
        Some(SearchPiece::Knight(SearchColor::White, Position::new(7, 0)))
    );
}
