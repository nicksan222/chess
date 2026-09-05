use chess::{Difficulty, GameSession, Player};

#[test]
fn player_kind_can_be_selected_at_runtime() {
    let online = true;
    let black = if online {
        Player::online()
    } else {
        Player::computer(Difficulty::Medium)
    };
    let session = GameSession::new(Player::human(), black);

    assert_eq!(session.black().difficulty(), None);
}
