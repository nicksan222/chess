use chess::{
    Board, CastlingRights, ChessMove, Color, FullmoveNumber, Game, GameStatus, HalfmoveClock,
    MoveError, Piece, PieceKind, Square,
};

fn board_with(pieces: impl IntoIterator<Item = Piece>) -> Board {
    Board::from_pieces(pieces)
}

fn play(game: &mut Game, from: Square, to: Square) {
    let piece = game.piece_at(from).expect("piece exists");
    piece.move_to(to, game).expect("move is legal");
}

fn perft(game: &Game, depth: u8) -> u64 {
    if depth == 0 {
        return 1;
    }
    let moves = game.legal_moves().collect::<Vec<_>>();

    moves
        .into_iter()
        .map(|chess_move| {
            let mut next = game.clone();
            chess_move.play(&mut next).unwrap();
            perft(&next, depth - 1)
        })
        .sum()
}

#[test]
fn initial_legal_move_tree_matches_standard_perft_counts() {
    let game = Game::new();

    assert_eq!(perft(&game, 1), 20);
    assert_eq!(perft(&game, 2), 400);
    assert_eq!(perft(&game, 3), 8_902);
    assert_eq!(perft(&game, 4), 197_281);
}

#[test]
fn pieces_report_legal_destinations_and_move_themselves() {
    let mut game = Game::new();
    let pawn = game.piece_at(Square::E2).unwrap();
    let knight = game.piece_at(Square::G1).unwrap();

    assert_eq!(
        pawn.legal_destinations(game.board())
            .iter()
            .collect::<Vec<_>>(),
        [Square::E3, Square::E4]
    );
    assert_eq!(
        knight
            .legal_destinations(game.board())
            .iter()
            .collect::<Vec<_>>(),
        [Square::F3, Square::H3]
    );

    let step = pawn.move_to(Square::E4, &mut game).unwrap();
    assert_eq!(step.chess_move(), ChessMove::new(Square::E2, Square::E4));
    assert_eq!(game.piece_at(Square::E2), None);
    assert_eq!(
        game.piece_at(Square::E4),
        Some(Piece::new(Color::White, PieceKind::Pawn, Square::E4))
    );
    assert_eq!(game.side_to_move(), Color::Black);
    assert_eq!(game.board().en_passant_target(), Some(Square::E3));
    assert_eq!(game.board().halfmove_clock(), HalfmoveClock::ZERO);
}

#[test]
fn stale_wrong_side_and_unreachable_moves_are_rejected_without_history() {
    let mut game = Game::new();
    let pawn = game.piece_at(Square::E2).unwrap();

    assert!(matches!(
        ChessMove::new(Square::E7, Square::E5).play(&mut game),
        Err(MoveError::WrongSide { .. })
    ));
    assert!(matches!(
        pawn.move_to(Square::E5, &mut game),
        Err(MoveError::IllegalDestination { .. })
    ));
    play(&mut game, Square::E2, Square::E4);
    assert_eq!(
        pawn.move_to(Square::E3, &mut game),
        Err(MoveError::StalePiece)
    );
    assert_eq!(game.history().len().value(), 1);
}

#[test]
fn pinned_pieces_cannot_expose_their_king() {
    let board = board_with([
        Piece::new(Color::White, PieceKind::King, Square::E1),
        Piece::new(Color::White, PieceKind::Rook, Square::E2),
        Piece::new(Color::Black, PieceKind::Rook, Square::E8),
        Piece::new(Color::Black, PieceKind::King, Square::G8),
    ]);
    let rook = board.piece_at(Square::E2).unwrap();
    let destinations = rook.legal_destinations(&board);

    assert!(!destinations.contains(Square::D2));
    assert!(destinations.contains(Square::E3));
    assert!(destinations.contains(Square::E8));
}

#[test]
fn castling_moves_both_self_locating_pieces() {
    let mut board = board_with([
        Piece::new(Color::White, PieceKind::Rook, Square::A1),
        Piece::new(Color::White, PieceKind::King, Square::E1),
        Piece::new(Color::White, PieceKind::Rook, Square::H1),
        Piece::new(Color::Black, PieceKind::Rook, Square::A8),
        Piece::new(Color::Black, PieceKind::King, Square::E8),
        Piece::new(Color::Black, PieceKind::Rook, Square::H8),
    ]);
    board.set_castling_rights(CastlingRights::ALL);
    let mut game = Game::from_board(board);
    let king = game.piece_at(Square::E1).unwrap();

    assert!(king.legal_destinations(game.board()).contains(Square::G1));
    assert!(king.legal_destinations(game.board()).contains(Square::C1));
    king.move_to(Square::G1, &mut game).unwrap();

    assert_eq!(game.piece_at(Square::E1), None);
    assert_eq!(game.piece_at(Square::H1), None);
    assert_eq!(game.piece_at(Square::G1).unwrap().kind(), PieceKind::King);
    assert_eq!(game.piece_at(Square::G1).unwrap().square(), Square::G1);
    assert_eq!(game.piece_at(Square::F1).unwrap().kind(), PieceKind::Rook);
    assert_eq!(game.piece_at(Square::F1).unwrap().square(), Square::F1);
}

#[test]
fn en_passant_and_selected_promotion_are_applied() {
    let mut game = Game::new();
    play(&mut game, Square::E2, Square::E4);
    play(&mut game, Square::A7, Square::A6);
    play(&mut game, Square::E4, Square::E5);
    play(&mut game, Square::D7, Square::D5);

    let pawn = game.piece_at(Square::E5).unwrap();
    assert!(pawn.legal_destinations(game.board()).contains(Square::D6));
    pawn.move_to(Square::D6, &mut game).unwrap();
    assert_eq!(game.piece_at(Square::D5), None);
    assert_eq!(game.piece_at(Square::D6).unwrap().square(), Square::D6);

    let mut board = board_with([
        Piece::new(Color::White, PieceKind::King, Square::H1),
        Piece::new(Color::White, PieceKind::Pawn, Square::A7),
        Piece::new(Color::Black, PieceKind::King, Square::H8),
    ]);
    board.set_fullmove_number(FullmoveNumber::new(40).unwrap());
    let mut promotion = Game::from_board(board);
    let pawn = promotion.piece_at(Square::A7).unwrap();
    let promotion_choices = pawn
        .legal_moves(promotion.board())
        .map(ChessMove::promotion_kind)
        .collect::<Vec<_>>();
    assert_eq!(
        promotion_choices,
        [
            Some(PieceKind::Knight),
            Some(PieceKind::Bishop),
            Some(PieceKind::Rook),
            Some(PieceKind::Queen),
        ]
    );

    let step = pawn
        .move_and_promote(Square::A8, PieceKind::Knight, &mut promotion)
        .unwrap();
    assert_eq!(step.chess_move().promotion_kind(), Some(PieceKind::Knight));
    assert_eq!(
        promotion.piece_at(Square::A8).unwrap().kind(),
        PieceKind::Knight
    );
    assert_eq!(
        promotion.board().fullmove_number(),
        FullmoveNumber::new(40).unwrap()
    );
}

#[test]
fn game_reports_pieces_side_to_move_and_check() {
    let game = Game::new();

    assert_eq!(game.side_to_move(), Color::White);
    assert!(!game.is_in_check());
    assert_eq!(game.pieces().len(), 32);
    assert_eq!(game.into_iter().count(), 32);

    let mut board = board_with([
        Piece::new(Color::White, PieceKind::King, Square::E1),
        Piece::new(Color::White, PieceKind::Queen, Square::E5),
        Piece::new(Color::Black, PieceKind::King, Square::E8),
    ]);
    board.set_side_to_move(Color::Black);
    let checked = Game::from_board(board);

    assert_eq!(checked.side_to_move(), Color::Black);
    assert!(checked.is_in_check());
    assert_eq!(checked.status(), GameStatus::InProgress);
    assert!(!checked.is_checkmate());
    assert!(!checked.is_stalemate());
    assert_eq!(
        checked.pieces().collect::<Vec<_>>(),
        [
            Piece::new(Color::White, PieceKind::King, Square::E1),
            Piece::new(Color::White, PieceKind::Queen, Square::E5),
            Piece::new(Color::Black, PieceKind::King, Square::E8),
        ]
    );
}

#[test]
fn game_reports_checkmate_and_stalemate() {
    let game = Game::new();
    assert_eq!(game.status(), GameStatus::InProgress);
    assert!(!game.is_checkmate());
    assert!(!game.is_stalemate());

    let mut mate = board_with([
        Piece::new(Color::White, PieceKind::King, Square::E1),
        Piece::new(Color::White, PieceKind::Rook, Square::A8),
        Piece::new(Color::Black, PieceKind::King, Square::E8),
        Piece::new(Color::Black, PieceKind::Pawn, Square::D7),
        Piece::new(Color::Black, PieceKind::Pawn, Square::E7),
        Piece::new(Color::Black, PieceKind::Pawn, Square::F7),
    ]);
    mate.set_side_to_move(Color::Black);
    let mated = Game::from_board(mate);
    assert!(mated.is_in_check());
    assert_eq!(
        mated.status(),
        GameStatus::Checkmate {
            winner: Color::White
        }
    );
    assert!(mated.is_checkmate());
    assert!(!mated.is_stalemate());

    let mut stale = board_with([
        Piece::new(Color::White, PieceKind::King, Square::A6),
        Piece::new(Color::White, PieceKind::Queen, Square::C7),
        Piece::new(Color::Black, PieceKind::King, Square::A8),
    ]);
    stale.set_side_to_move(Color::Black);
    let stalemated = Game::from_board(stale);
    assert!(!stalemated.is_in_check());
    assert_eq!(stalemated.status(), GameStatus::Stalemate);
    assert!(!stalemated.is_checkmate());
    assert!(stalemated.is_stalemate());
}
