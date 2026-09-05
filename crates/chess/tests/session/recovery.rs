use chess::{
    ChessMove, DrawClaim, GameSession, GameStatus, HistoryEvent, Player, SessionError,
    SessionUpdate, Square,
};

#[test]
fn rejected_player_moves_follow_authoritative_game_semantics() {
    let mut session = GameSession::new(Player::human(), Player::human());
    session
        .white_mut()
        .submit(ChessMove::new(Square::E2, Square::E5))
        .unwrap();

    assert!(matches!(
        session.poll(),
        Err(SessionError::MoveRejected {
            player: chess::Color::White,
            ..
        })
    ));
    assert!(session.game().latest_invalid().is_some());
    assert!(matches!(
        session.poll(),
        Ok(SessionUpdate::Unavailable(
            chess::GameStatus::Invalid { .. }
        ))
    ));
}

#[test]
fn session_resolves_invalid_without_destructuring() {
    let mut session = GameSession::new(Player::human(), Player::human());
    session
        .white_mut()
        .submit(ChessMove::new(Square::E2, Square::E5))
        .unwrap();
    assert!(matches!(
        session.poll(),
        Err(SessionError::MoveRejected { .. })
    ));
    assert!(matches!(session.status(), GameStatus::Invalid { .. }));

    session
        .resolve_latest_invalid()
        .expect("session resolves the rejected move");
    assert_eq!(session.status(), GameStatus::InProgress);

    let white_move = ChessMove::new(Square::E2, Square::E4);
    session.white_mut().submit(white_move).unwrap();
    let update = session.poll().expect("play resumes after resolution");
    assert!(matches!(
        update,
        SessionUpdate::MovePlayed {
            player: chess::Color::White,
            step
        } if step.event() == HistoryEvent::Move(white_move)
    ));
}

#[test]
fn session_claim_draw_unavailable_records_invalid_and_resolves() {
    let mut session = GameSession::new(Player::human(), Player::human());
    assert!(matches!(
        session.claim_draw(DrawClaim::FiftyMoveRule),
        Err(chess::DrawClaimError::Unavailable { .. })
    ));
    assert!(matches!(session.status(), GameStatus::Invalid { .. }));
    session
        .resolve_latest_invalid()
        .expect("unavailable claim resolves like a rejected move");
    assert_eq!(session.status(), GameStatus::InProgress);
}
