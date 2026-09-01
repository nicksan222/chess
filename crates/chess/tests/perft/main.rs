#[path = "../common/mod.rs"]
mod common;

use chess::Game;
use common::perft;

#[test]
fn initial_position_matches_standard_perft_counts() {
    let game = Game::new();

    assert_eq!(perft::count(&game, 1), 20);
    assert_eq!(perft::count(&game, 2), 400);
    assert_eq!(perft::count(&game, 3), 8_902);
    assert_eq!(perft::count(&game, 4), 197_281);
}

#[test]
fn kiwipete_matches_standard_perft_counts() {
    let game = perft::kiwipete();

    assert_eq!(perft::count(&game, 1), 48);
    assert_eq!(perft::count(&game, 2), 2_039);
    assert_eq!(perft::count(&game, 3), 97_862);
}
