# Chess crate design

This crate is the game. Firmware, the simulator, persistence, transport, and
tests consume it as a library. They do not reach into `model/` or `game/`, and
they do not share a protocol with this package. The public surface is the crate
root.

The design question is not how the engine is implemented. It is how a consumer
should talk to it: which type they hold, which method they call, and which
values they are allowed to send across a process, a wire, or a store.

## Package shape

`chess` is a `no_std` library with no crate features, no public modules, and no
`unsafe`. The crate root re-exports every type a consumer needs:

```rust
use chess::{ChessMove, Game, HistoryEvent, Square};
```

Internal modules stay private so the filesystem can change without changing
callers. Adding a public module would split the API into an internal map of the
source tree. The package is a vocabulary of chess values plus one aggregate.

Dependencies stay small and one-way. `chess-core` supplies the linked list used
by history. `logger` is an optional diagnostic facade. `sha2` hashes history
with default features disabled. Hardware crates, UI crates, persistence
backends, and async runtimes are not dependencies and must not become
dependencies.

Board values, piece movement, and legal-move generation are allocation-free.
`GameHistory` is the deliberate allocation boundary: it retains events in
`chess-core`'s linked list. That is the only reason a hosted or embedded
consumer needs an allocator.

## What a consumer holds

There are two kinds of values, and they are not interchangeable.

**Domain values** are notation-independent, `Copy`, and valid without a game.
`Square`, `Piece`, `PieceKind`, `Color`, `ChessMove`, `Board`, and `SquareSet`
describe a position or an intent. Firmware can map a Hall sensor to a `Square`
by index. A renderer can iterate `&Game` as self-locating `Piece` values. A
test can assemble a `Board` with `Board::from_pieces` and never create a
`Game`.

**The aggregate** is `Game`. It retains the initial board, a derived current
board, and one authoritative `GameHistory`. The board inside `Game` is a cache.
History is the source of truth. Consumers that need to continue a game, record
an illegal attempt, synchronize with a peer, or persist a match hold a `Game`.
Consumers that only need geometry or a snapshot hold values.

`Game` never hands out `&mut Board`. `board()` is read-only. Legal transitions
go through `Game`. Setup and physical-board edits that bypass rules stay on
`Board` and happen *before* `Game::from_board`, not against a live cache.

```text
consumer
   |
   |  play / accept / claim / resolve
   v
 Game  --read-only cache-->  Board, Piece, Square
   |
   |  authoritative timeline
   v
 GameHistory  of  HistoryStep     <-- persist, transport, verify
```

## Grammar

Methods live on the noun the caller already has.

| Caller has | Caller wants | Call |
|---|---|---|
| a `Game` | play a coordinate move | `game.play(chess_move)` |
| a `ChessMove` | play it | `chess_move.play(&mut game)` |
| a `Piece` from the board | move that piece | `piece.move_to(destination, &mut game)` |
| a promoting pawn | choose the kind | `piece.move_and_promote(destination, kind, &mut game)` |
| a `Game` | inspect legality | `game.legal_moves()` or `piece.legal_destinations(game.board())` |
| a `Game` | inspect lifecycle | `game.status()` |
| a `HistoryStep` from a peer | apply it | `game.accept(step)` |
| a `Board` being assembled | relocate without rules | `board.force_move(from, to)` |

That grammar is the package. Callers should not grow a parallel service object
that wraps `Game` in order to expose the same operations under different names.

`ChessMove` is intent, not a proven legal action. Construction does not consult
a board. Legality belongs to generation and to `Game::play` / `Board`
validation. Coordinate text such as `e2e4` and `e7e8q` parses with `FromStr`;
SAN, PGN, and FEN are application concerns.

`Piece` is self-locating: color, kind, and square travel together. After a
move, the piece on the destination is a new value at that square. Holding a
stale `Piece` and asking it to move again returns `MoveError::StalePiece` and
records an invalid event. That is intentional. Physical firmware should read
the piece from the current board, not reuse a value from an earlier ply.

Squares are indexed `a1 = 0` through `h8 = 63`, file-major then rank-major.
`Square::E2` and `"e2".parse()` are the same value. Hardware adapters should
use `Square` / `SquareIndex`, not invent a second numbering scheme.

## Local play

A hosted application starts a standard match with `Game::new()`, or a custom
position with `Game::from_board`. From that point the write path is small:

```rust
use chess::{ChessMove, Game, HistoryEvent, Square};

let mut game = Game::new();
let step = game.play(ChessMove::new(Square::E2, Square::E4))?;
assert!(matches!(step.event(), HistoryEvent::Move(_)));
# Ok::<(), chess::MoveError>(())
```

`play` returns the `HistoryStep` that was appended. That step is the value to
log, persist, or send. The method also finalizes automatically when the move
leaves checkmate, stalemate, insufficient material, fivefold repetition, or
the seventy-five-move rule.

`Game::from_board` does the same terminal check on construction. A kings-only
setup is born already sealed; callers do not have to notice and finalize it.

Default pawn promotion is a queen. `Piece::move_to` onto the back rank takes
that default. Selecting a knight, bishop, or rook requires
`Piece::move_and_promote` or `ChessMove::promotion`. A promotion kind on a
non-promoting move is `MoveError::UnexpectedPromotion`.

`legal_moves` is empty when history is invalid or final. Querying a `Board`
directly still reports chess-legal destinations for that snapshot; `Game`
additionally respects the history tip. Firmware that lights legal squares
during play should ask the `Game`, not a copied board that cannot see an
unresolved invalid event.

## Observation

Read paths do not clone the aggregate.

- `game.board()` and `game.piece_at(square)` are the position cache.
- `game.pieces()` and `for piece in &game` iterate self-locating pieces.
- `game.side_to_move()` and `game.is_in_check()` are position queries.
- `game.status()` is the lifecycle value a UI should match on.
- `game.history()` is the immutable timeline.
- `game.draw_claims()` is the set the side to move may claim *now*.
- `game.latest_invalid()` is the newest blocking error, if any.

`GameStatus` distinguishes in-progress play, available claims, unresolved
invalid operations, checkmate, stalemate, and completed draws.
`status().is_terminal()` is the flag for "accept no further legal play."
Convenience predicates (`is_checkmate`, `is_stalemate`, `is_draw`) exist so
callers do not re-match the enum for the common questions.

Menu code can borrow `&Game` as frozen context while firmware keeps mutable
hardware state elsewhere. This crate never requires ownership of the
application, a display, or an input device.

## Invalid operations

Rejected play is not thrown away. `Game::play`, failed draw claims, and failed
synchronization append `HistoryEvent::Invalid` and leave the board cache
unchanged. While an invalid event is newest:

- legal moves are unavailable;
- a further legal-looking play appends `InvalidState::PendingInvalid`;
- only another invalid event, or resolving the latest invalid, is allowed;
- a final event is refused.

Resolution is stack discipline: `Game::resolve_latest_invalid` removes only
the newest invalid event. Firmware that models a lifted piece, an extra
sensor trip, or a retracted claim should record the failure, present it, and
resolve newest-first. Do not attempt to splice a valid move under an
unresolved error.

A final event accepts no successor. The game is sealed.

## Draws

The engine distinguishes claims from automatic results, and callers must too.

| Situation | Consumer action |
|---|---|
| Threefold repetition or fifty-move rule | Read `draw_claims()`, then `claim_draw` if the player claims |
| A claim that would become available after a legal move | `draw_claims_after(move)` then `claim_draw_after(move, claim)` |
| Fivefold repetition, seventy-five-move rule, insufficient material | None. `play` / construction already appended `FinalState::Draw` |
| Checkmate or stalemate | None. Those outrank remaining draw claims |

`claim_draw_after` retains the announced move as evidence and does **not**
play it. Under the Laws of Chess a valid claim ends the game immediately.
Unavailable claims become invalid events and must be resolved like any other
rejection.

Position identity for repetition is placement, side to move, castling rights,
and an en-passant target only when a legal en-passant capture exists.
Halfmove and fullmove clocks are not part of that identity. Callers that
implement a second repetition detector should not invent a different key.

## Synchronization and persistence

The unit that leaves the process is `HistoryStep`: ply, event, previous hash,
and cumulative SHA-256 hash. It is `Copy`. Transport and stores should
exchange steps, not ad-hoc move lists and not `Debug` text.

Two append paths exist, and they are not equivalent:

- `Game::accept` is the consumer API for a peer or a loaded log. It checks
  sequence, previous hash, event hash, structural transition, move legality,
  canonical promotion, and the meaning of a final event. Success updates the
  board cache and derives automatic finals exactly as local `play` does.
  Failure records `InvalidState::Synchronization` unless history is already
  sealed.
- `GameHistory::try_append` checks hashes and structural transitions only. It
  cannot see chess. Do not use it to apply a peer's move to a `Game`.

`GameHistory::push` is for building a local chain when the caller already has
an event. `Game` uses it internally. Application code that is playing chess
should call `play`, `claim_draw`, `accept`, or `resolve_latest_invalid`
instead of assembling events by hand.

After load, call `Game::verify`. It recomputes the hash chain, replays move
events from the retained initial board, confirms the cache, and checks that
any final event is still valid for the reproduced position.
`rebuild_board` is the same replay without trusting the cache; use it when
diagnosing a mismatch.

Authentication is not in this crate. The hash chain detects corruption and
divergence. It does not name a peer. Signatures, pairing, and transport
integrity belong to the application.

## Setup and the physical board

Construct positions with values, then wrap them:

```rust
use chess::{Board, Color, Game, Piece, PieceKind, Square};

let mut board = Board::from_pieces([
    Piece::new(Color::White, PieceKind::King, Square::E1),
    Piece::new(Color::Black, PieceKind::King, Square::E8),
]);
board.set_side_to_move(Color::White);
let game = Game::from_board(board);
```

`Board::force_move` relocates a piece without movement rules, clocks,
castling, en passant, or history. `Square::force_move_to` is the same
operation from the origin square. This is for assembling a snapshot or
reconciling a physical displacement that is *not* a chess move. It is not a
back door into a live `Game`. Compare the sensor map to `game.board()`, then
either `play` the matching legal move or record an invalid operation.

Clocks, castling rights, and the en-passant target are explicit board fields
with typed setters. There is no FEN parser here. An application that speaks
FEN should decode into these fields itself.

## Logging

The engine looks at the process-wide `logger` singleton. With no registration,
every operation is silent. Registration is the application's job, once, at
startup:

```rust
use logger::{LevelFilter, implementations::SystemdLogger, register};

static LOGGER: SystemdLogger = SystemdLogger::new(LevelFilter::Info);
register(&LOGGER)?;
# Ok::<(), logger::RegistrationError>(())
```

Lifecycle diagnostics use the target `chess::game`. Creation is debug;
accepted moves, resolutions, and terminal results are info; invalid states are
warn. Consumers should not parse log text. The return values and `HistoryStep`
events are the API. Logs are optional observation.

This crate does not select a backend, flush policy, or log level.

## What stays outside

Keep these in applications and adapters:

- GPIO, I²C, SPI, LEDs, buttons, OLED layout, and sensor debounce
- SAN, PGN, FEN, UCI, and opening books
- Clocks as in chess clocks, matchmaking, and ratings
- Persistence backends, files, and databases
- Network framing, retries, and authentication
- Search, evaluation, and engines that pick a move
- Async runtimes and threads

`Board::legal_moves` is a rules query, not a search API. If a future AI
adapter needs generation, it consumes this crate the same way firmware does.

## Hash encodings

History hashing is a public contract even though the digest functions are
private. Peer implementations and stored games depend on it remaining stable:

- domain `chess.game-history.sha256.v1` for events
- domain `chess.board-anchor.sha256.v1` for the initial board
- explicit integer tags for event kind, invalid kind, final kind, colors,
  piece kinds, promotion, and draw reasons
- big-endian ply and clock bytes
- the complete prior chain, not only the previous tip's display form

Do not hash `Debug` output. Do not change a tag without treating it as a
breaking change to every stored and in-flight `HistoryStep`. Equal event
streams from different initial boards must not synchronize: the chain is
anchored to the starting position.

## Source layout

The source tree is organized for maintainers, not for consumers. `src/README.md`
covers that map. Externally, the rule is: import from `chess`, hold a `Game`
when the match is live, hold `HistoryStep` when the match leaves the process,
and hold `Board` / `Piece` / `Square` when you are describing a position.
