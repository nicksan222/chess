use chess::{
    Board, CastlingRights, ChessMove, Color, ComputerError, Difficulty, Game, GameSession,
    HistoryEvent, Piece, PieceKind, Player, PlayerError, SessionError, SessionUpdate, Square,
};

#[test]
fn computer_players_use_the_same_player_model() {
    let mut session = GameSession::new(Player::computer(Difficulty::Beginner), Player::human());

    assert!(matches!(
        session.poll().unwrap(),
        SessionUpdate::MovePlayed {
            player: Color::White,
            ..
        }
    ));
}

#[test]
fn computer_illegal_engine_move_surfaces_error_without_polluting_history() {
    let board = Board::from_pieces([
        Piece::new(Color::White, PieceKind::King, Square::E1),
        Piece::new(Color::White, PieceKind::Bishop, Square::D1),
        Piece::new(Color::White, PieceKind::Bishop, Square::F1),
        Piece::new(Color::White, PieceKind::Pawn, Square::D2),
        Piece::new(Color::White, PieceKind::Pawn, Square::E2),
        Piece::new(Color::White, PieceKind::Pawn, Square::F2),
        Piece::new(Color::Black, PieceKind::King, Square::H8),
        Piece::new(Color::Black, PieceKind::Knight, Square::F3),
        Piece::new(Color::Black, PieceKind::Pawn, Square::D3),
    ]);
    let game = Game::from_board(board);
    let forced = ChessMove::new(Square::E2, Square::F3);
    assert_eq!(game.legal_moves().collect::<Vec<_>>(), [forced]);
    let mut session = GameSession::from_game(
        game,
        Player::computer(Difficulty::Beginner),
        Player::human(),
    );

    match session.poll() {
        Err(SessionError::Player {
            player: Color::White,
            error: PlayerError::Computer(ComputerError::IllegalMove(_)),
        }) => {}
        Err(SessionError::Player {
            player: Color::White,
            error: PlayerError::Computer(ComputerError::Resigned),
        }) => {}
        Ok(SessionUpdate::MovePlayed { step, .. }) => {
            assert_eq!(step.event(), HistoryEvent::Move(forced));
        }
        other => panic!("computer divergence must error or play the forced move: {other:?}"),
    }
    // A computer failure never appends invalid history, unlike a rejected
    // human move through `Game::play`.
    assert!(session.game().latest_invalid().is_none());
}

#[test]
fn computer_castling_divergence_surfaces_error_instead_of_silent_substitution() {
    let mut board = Board::from_pieces([
        Piece::new(Color::White, PieceKind::King, Square::H1),
        Piece::new(Color::White, PieceKind::Rook, Square::A1),
        Piece::new(Color::White, PieceKind::Queen, Square::C7),
        Piece::new(Color::Black, PieceKind::King, Square::A8),
    ]);
    let mut rights = CastlingRights::NONE;
    rights.grant_queenside(Color::White);
    board.set_castling_rights(rights);
    let game = Game::from_board(board);
    // The recorded rights describe queenside castling while the king stands on
    // H1, so the engine and domain disagree about castling legality.
    let mut session = GameSession::from_game(
        game,
        Player::computer(Difficulty::Beginner),
        Player::human(),
    );

    match session.poll() {
        Err(SessionError::Player {
            player: Color::White,
            error: PlayerError::Computer(_),
        }) => {}
        Ok(SessionUpdate::MovePlayed { step, .. }) => {
            assert_ne!(
                step.event(),
                HistoryEvent::Move(ChessMove::new(Square::E1, Square::C1))
            );
        }
        other => panic!("castling divergence must error or play a legal move: {other:?}"),
    }
    assert!(session.game().latest_invalid().is_none());
}

#[test]
fn difficulties_order_by_strength_with_medium_default() {
    assert!(Difficulty::Beginner < Difficulty::Easy);
    assert!(Difficulty::Easy < Difficulty::Medium);
    assert!(Difficulty::Medium < Difficulty::Hard);
    assert!(Difficulty::Hard < Difficulty::Expert);
    assert_eq!(Difficulty::default(), Difficulty::Medium);
}
