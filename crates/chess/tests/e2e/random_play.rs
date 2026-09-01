use std::thread;

use chess::Game;

use crate::common::perft;

const WORKER_COUNT: u64 = 8;
const GAMES_PER_WORKER: u64 = 2;
const MAX_PLIES: usize = 128;

#[derive(Clone, Copy)]
struct XorShift64(u64);

impl XorShift64 {
    fn next(&mut self) -> u64 {
        self.0 ^= self.0 << 13;
        self.0 ^= self.0 >> 7;
        self.0 ^= self.0 << 17;
        self.0
    }
}

#[test]
fn randomized_legal_games_replay_verify_and_synchronize_in_parallel() {
    // Kiwipete comes from the public Chess Programming Wiki perft suite:
    // https://www.chessprogramming.org/Perft_Results
    thread::scope(|scope| {
        for worker in 0..WORKER_COUNT {
            scope.spawn(move || {
                for game_index in 0..GAMES_PER_WORKER {
                    let mut sender = if game_index % 2 == 0 {
                        Game::new()
                    } else {
                        perft::kiwipete()
                    };
                    let mut receiver = sender.clone();
                    let seed = 0x9e37_79b9_7f4a_7c15_u64
                        .wrapping_mul(worker * GAMES_PER_WORKER + game_index + 1);
                    let mut random = XorShift64(seed);

                    for ply in 0..MAX_PLIES {
                        let moves = sender.legal_moves().collect::<Vec<_>>();
                        if moves.is_empty() {
                            assert!(sender.status().is_terminal(), "worker {worker}, game {game_index}, ply {ply}");
                            break;
                        }

                        let chess_move = moves[(random.next() as usize) % moves.len()];
                        let step = sender.play(chess_move).unwrap_or_else(|error| {
                            panic!(
                                "generated move {chess_move} failed for worker {worker}, game {game_index}, ply {ply}: {error}"
                            )
                        });
                        receiver.accept(step).unwrap_or_else(|error| {
                            panic!(
                                "move {chess_move} failed to synchronize for worker {worker}, game {game_index}, ply {ply}: {error}"
                            )
                        });

                        assert_eq!(sender, receiver, "worker {worker}, game {game_index}, ply {ply}");
                    }

                    assert_eq!(
                        sender.verify(),
                        Ok(()),
                        "sender verification failed for worker {worker}, game {game_index}"
                    );
                    assert_eq!(
                        receiver.verify(),
                        Ok(()),
                        "receiver verification failed for worker {worker}, game {game_index}"
                    );
                }
            });
        }
    });
}
