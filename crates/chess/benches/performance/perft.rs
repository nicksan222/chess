#[path = "../../tests/common/perft.rs"]
mod perft;

use std::{hint::black_box, time::Instant};

use chess::Game;

fn benchmark(name: &str, game: &Game, depth: u8, expected_nodes: u64) {
    const SAMPLE_COUNT: u32 = 5;

    let started = Instant::now();
    for _ in 0..SAMPLE_COUNT {
        let nodes = perft::count(black_box(game), black_box(depth));
        assert_eq!(nodes, expected_nodes);
        black_box(nodes);
    }
    let elapsed = started.elapsed();
    let total_nodes = expected_nodes * u64::from(SAMPLE_COUNT);
    let nodes_per_second = total_nodes as f64 / elapsed.as_secs_f64();

    println!("{name}: {nodes_per_second:.0} nodes/s ({SAMPLE_COUNT} samples in {elapsed:.3?})");
}

fn main() {
    if cfg!(debug_assertions) {
        // Keep `cargo test --all-targets` fast; `cargo bench` uses the release cases below.
        benchmark("initial depth 2 (debug smoke test)", &Game::new(), 2, 400);
        benchmark(
            "Kiwipete depth 1 (debug smoke test)",
            &perft::kiwipete(),
            1,
            48,
        );
    } else {
        benchmark("initial depth 4", &Game::new(), 4, 197_281);
        benchmark("Kiwipete depth 3", &perft::kiwipete(), 3, 97_862);
    }
}
