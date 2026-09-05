use chess::{ChessMove, Color, GameSession, HistoryEvent, Player, SessionUpdate, Square};

#[test]
fn session_polls_only_the_side_to_move_and_commits_its_move() {
    let mut session = GameSession::new(Player::human(), Player::online());
    let white_move = ChessMove::new(Square::E2, Square::E4);
    session.white_mut().submit(white_move).unwrap();

    let update = session.poll().unwrap();
    assert!(matches!(
        update,
        SessionUpdate::MovePlayed {
            player: Color::White,
            step
        } if step.event() == HistoryEvent::Move(white_move)
    ));
    assert_eq!(session.game().side_to_move(), Color::Black);
    assert_eq!(
        session.poll().unwrap(),
        SessionUpdate::Pending {
            player: Color::Black
        }
    );
}
