# Lichess puzzle regression tests

`lichess` is a normal Cargo integration-test target, included in the chess package's
`test` and `check` recipes. It runs offline with no additional Rust dependencies:

```sh
cargo test --package chess --test lichess
```

## Source and selection

The source is the [Lichess puzzle database](https://database.lichess.org/#puzzles),
released under [CC0 1.0](https://creativecommons.org/publicdomain/zero/1.0/).
`fixtures/puzzles.tsv` retains the original puzzle IDs, FENs, UCI move sequences, and
themes. A puzzle can be inspected at `https://lichess.org/training/<PuzzleId>`.
Lichess's FEN precedes the opponent's first move; the tests replay **every** move,
including that setup move.

Retrieved on 2026-10-20 from
`https://database.lichess.org/lichess_db_puzzle.csv.zst`. Selection used the complete
CSV rows decoded from bytes 0–4194303 (inclusive) of that compressed export:
82,852 rows. In source order, take the first 128 puzzles, then append the first
eight for each theme `castling`, `enPassant`, `promotion`, `underPromotion`,
`mateIn1`, `mateIn2`, `stalemate`, and `long`, deduplicating by ID and preserving
first insertion order. No stalemate-tagged puzzle occurred in that prefix.
This yields 157 puzzles; selection did not depend on the Rust engine's results.
The upstream export changes over time, so tests use the checked-in snapshot.

Source subset SHA-256 (`puzzles.tsv`):
`6203b84bb5d8676644d33b1181c3a1cd5d42e84718b1295b6943b9ba7f392d76`.

## Independent expectations

`fixtures/expected_positions.tsv` is a fixed reference snapshot, originally validated with
[python-chess](https://github.com/niklasf/python-chess) version **1.11.2**,
independently of the Rust engine. It contains the initial state and every
subsequent state: complete six-field FEN (including the raw en-passant target
after double pushes), sorted legal UCI moves, check flag, and position status.
The corpus consists only of TSV data and Rust tests; no generator or Python
dependency is included or required. Changes to reference expectations should be
independently verified rather than derived from the engine under test.

The 764 moves include eight castles, eight en-passant captures, 18 promotions
(nine underpromotions), and 37 resulting checkmates. Across all 921 positions,
the harness compares complete board metadata, exact legal move sets (detecting
both missing and extra moves), check and status. It also applies each published
move through `Game::play`, synchronizes the resulting event with `Game::accept`,
and verifies both hash chains and board replay at every ply. Separate negative
cases choose a move absent from the independent legal set in each of the 884
active positions after replaying the published history. They assert the specific
illegal-destination error, check rejection without board mutation, and resolve the
invalid event to recover the exact prior game. Typed fixture loading also checks
unique puzzle IDs, consecutive plies, published moves and initial FENs, and corpus
size before any engine assertions run.

This is a rules and history regression corpus, not a puzzle-solving benchmark:
it does not require the computer player to choose the published tactical move.
It complements the existing perft and focused draw-rule tests. These short lines
do not provide independent coverage of repetition claims or long move-count draws.
