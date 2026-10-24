#![allow(
    clippy::unwrap_used,
    clippy::expect_used,
    clippy::panic,
    reason = "integration-test helpers panic to report a failure"
)]

mod fen;
mod puzzles;

use chess::{ChessMove, Game, HistoryEvent, MoveError, PieceKind, Square};

#[test]
fn lichess_lines_match_independent_positions_moves_and_history() {
    for puzzle in puzzles::load() {
        let mut sender = Game::from_board(puzzle.positions[0].board);
        let mut receiver = sender.clone();
        for expected in puzzle.positions {
            if let Some(chess_move) = expected.chess_move {
                let step = sender
                    .play(chess_move)
                    .unwrap_or_else(|error| panic!("{expected}: {error}"));
                assert_eq!(step.event(), HistoryEvent::Move(chess_move), "{expected}");
                receiver
                    .accept(step)
                    .unwrap_or_else(|error| panic!("sync {expected}: {error}"));
            }
            assert_eq!(*sender.board(), expected.board, "board {expected}");
            let mut board_moves: Vec<_> = sender.board().legal_moves().collect();
            board_moves.sort_unstable();
            assert_eq!(board_moves, expected.legal_moves, "board moves {expected}");
            let mut game_moves: Vec<_> = sender.legal_moves().collect();
            game_moves.sort_unstable();
            let playable = if expected.status.is_terminal() {
                &[][..]
            } else {
                expected.legal_moves.as_slice()
            };
            assert_eq!(game_moves, playable, "game moves {expected}");
            assert_eq!(sender.is_in_check(), expected.in_check, "check {expected}");
            assert_eq!(sender.status(), expected.status, "status {expected}");
            assert_eq!(sender, receiver, "synchronization {expected}");
            assert_eq!(sender.verify(), Ok(()), "sender replay {expected}");
            assert_eq!(receiver.verify(), Ok(()), "receiver replay {expected}");
        }
    }
}

#[test]
fn illegal_moves_preserve_replayed_positions_and_recover_the_exact_history() {
    let mut checked = 0;
    for puzzle in puzzles::load() {
        let mut game = Game::from_board(puzzle.positions[0].board);
        for expected in puzzle.positions {
            if let Some(chess_move) = expected.chess_move {
                game.play(chess_move)
                    .unwrap_or_else(|error| panic!("{expected}: {error}"));
            }
            if expected.status.is_terminal() {
                continue;
            }
            // Test movement/check rules with a friendly source and an empty or
            // enemy destination. Exclude king captures and legal promotions whose
            // omitted promotion kind Game::play would default to a queen.
            let illegal = game
                .pieces()
                .filter(|piece| piece.color() == game.side_to_move())
                .flat_map(|piece| Square::all().map(move |to| ChessMove::new(piece.square(), to)))
                .find(|candidate| {
                    candidate.from() != candidate.to()
                        && game.piece_at(candidate.to()).is_none_or(|piece| {
                            piece.color() != game.side_to_move() && piece.kind() != PieceKind::King
                        })
                        && !expected.legal_moves.iter().any(|legal| {
                            legal.from() == candidate.from() && legal.to() == candidate.to()
                        })
                })
                .expect("position offers an illegal candidate");
            let original = game.clone();
            assert_eq!(
                game.play(illegal),
                Err(MoveError::IllegalDestination {
                    from: illegal.from(),
                    to: illegal.to(),
                }),
                "{expected}, illegal {illegal}"
            );
            assert_eq!(game.board(), original.board(), "{expected}");
            assert!(game.latest_invalid().is_some(), "{expected}");
            assert_eq!(game.verify(), Ok(()), "invalid history {expected}");
            game.resolve_latest_invalid().unwrap();
            assert_eq!(game, original, "recovery {expected}");
            checked += 1;
        }
    }
    assert_eq!(checked, 884);
}
