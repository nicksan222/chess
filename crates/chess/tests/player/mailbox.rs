use chess::{ChessMove, Difficulty, Player, Square, SubmitError};

#[test]
fn submitted_moves_are_not_silently_overwritten() {
    let first = ChessMove::new(Square::E2, Square::E4);
    let mut player = Player::human();
    player.submit(first).unwrap();

    assert_eq!(
        player.submit(ChessMove::new(Square::D2, Square::D4)),
        Err(SubmitError::MovePending(first))
    );
    assert_eq!(player.pending_move(), Some(first));
    assert_eq!(player.cancel(), Some(first));
}

#[test]
fn human_and_online_share_external_mailbox_semantics() {
    let first = ChessMove::new(Square::E2, Square::E4);
    let mut human = Player::human();
    let mut online = Player::online();
    human.submit(first).unwrap();
    online.submit(first).unwrap();
    assert_eq!(human.pending_move(), Some(first));
    assert_eq!(online.pending_move(), Some(first));
    assert_eq!(human.cancel(), Some(first));
    assert_eq!(online.cancel(), Some(first));

    let mut computer = Player::computer(Difficulty::Medium);
    assert_eq!(computer.submit(first), Err(SubmitError::ComputerControlled));
    assert_eq!(computer.pending_move(), None);
    assert_eq!(computer.cancel(), None);
}
