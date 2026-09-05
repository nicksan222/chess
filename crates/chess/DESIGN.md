# Chess crate design

The crate root **is** the package. Firmware, the simulator, persistence,
transport, and tests import types from `chess`. They never import `model/` or
`game/`.

```mermaid
flowchart LR
    subgraph consumers["Consumers"]
        FW["firmware"]
        SIM["simulator"]
        STORE["persistence"]
        PEER["transport / peer"]
        TEST["tests"]
        MENU["menu context"]
    end

    subgraph chess["chess crate root"]
        GAME["Game"]
        VALUES["Square · Piece · Board · ChessMove"]
        STEP["HistoryStep"]
    end

    FW -->|"play / accept / claim"| GAME
    SIM -->|"play / status"| GAME
        MENU -->|"borrow Game"| GAME
    TEST --> GAME
    TEST --> VALUES
    STORE --> STEP
    PEER --> STEP
    GAME -.->|"read-only cache"| VALUES
    GAME -->|"authoritative timeline"| STEP
```

## Package shape

One namespace. No public modules. No crate features. No `unsafe`. `no_std`.

```mermaid
flowchart TB
    ROOT["use chess::{Game, Square, HistoryStep, ...}"]

    subgraph inside["Inside the crate — private"]
        MODEL["model/"]
        GAME_MOD["game/"]
    end

    subgraph deps["Dependencies — one way"]
        CORE["chess-core linked list"]
        LOG["logger facade"]
        SHA["sha2"]
    end

    subgraph never["Never dependencies"]
        HW["hardware / GPIO"]
        UI["OLED / buttons"]
        NET["sockets / async"]
        DB["SQLite / files"]
    end

    ROOT --> MODEL
    ROOT --> GAME_MOD
    GAME_MOD --> CORE
    GAME_MOD --> LOG
    GAME_MOD --> SHA
    ROOT -.->|"forbidden"| never
```

Board geometry, pieces, and legal-move generation allocate nothing.
`GameHistory` is the only allocation boundary.

```text
allocation-free ──────────────────────────── allocate
Square  Piece  Board  ChessMove  SquareSet   GameHistory
                                             (linked list of HistoryStep)
```

## Hold this

Two kinds of values. They are not interchangeable.

```mermaid
flowchart TB
    subgraph values["Domain values — Copy, no Game required"]
        SQ["Square"]
        PC["Piece"]
        BD["Board"]
        MV["ChessMove"]
        SS["SquareSet"]
    end

    subgraph aggregate["Aggregate — owns the match"]
        G["Game"]
        GH["GameHistory"]
        HS["HistoryStep"]
    end

    SQ --> PC
    PC --> BD
    SQ --> MV
    BD -->|"Game::from_board"| G
    G -->|"board() read-only"| BD
    G --> GH
    GH --> HS
```

| You are doing | You hold |
|---|---|
| Mapping a Hall sensor, lighting a square, rendering a piece | `Square`, `Piece`, `Board` |
| Playing, claiming, resolving, synchronizing a match | `Game` |
| Writing to a store or a peer | `HistoryStep` |

`Game` never yields `&mut Board`. Setup and physical-board edits that bypass
rules happen on a `Board` **before** `Game::from_board`.

```text
                    Game
        ┌─────────────┼─────────────┐
        │             │             │
   initial_board   board()      history()
   (anchor)        cache        source of truth
        │             │             │
        └──── replay move events ───┘
                    │
                 verify()
```

## Grammar

Methods live on the noun the caller already has.

```mermaid
flowchart LR
    P["Piece from the board"] -->|"move_to"| G["Game"]
    C["ChessMove"] -->|"play"| G
    G -->|"returns"| STEP["HistoryStep"]
    PEER["peer HistoryStep"] -->|"accept"| G
    B["Board being assembled"] -->|"force_move"| FM["ForcedMove"]
```

| Caller has | Caller wants | Call |
|---|---|---|
| `Game` | play a coordinate move | `game.play(chess_move)` |
| `ChessMove` | play it | `chess_move.play(&mut game)` |
| `Piece` | move that piece | `piece.move_to(to, &mut game)` |
| promoting pawn | choose the kind | `piece.move_and_promote(to, kind, &mut game)` |
| `Game` | legal squares / status | `game.legal_moves()` / `game.status()` |
| peer `HistoryStep` | apply it | `game.accept(step)` |
| `Board` | relocate without rules | `board.force_move(from, to)` |

`ChessMove` is intent. Construction does not consult a board. `"e2e4"` and
`"e7e8q"` parse with `FromStr`. SAN, PGN, and FEN stay in the application.

`Piece` is self-locating:

```text
┌─────────┬──────────┬─────────┐
│  color  │   kind   │ square  │
│  White  │   Pawn   │   e2    │
└─────────┴──────────┴─────────┘
        move_to(e4)
                │
                v
┌─────────┬──────────┬─────────┐
│  color  │   kind   │ square  │
│  White  │   Pawn   │   e4    │
└─────────┴──────────┴─────────┘
```

Reuse the old `Piece` and `move_to` returns `StalePiece`. Firmware reads the
piece from the current board every ply.

## Squares are the hardware map

Index `0 = a1` through `63 = h8`. Rank-major: files run fastest.

```text
index = rank × 8 + file
        rank 0 = 1 … rank 7 = 8
        file 0 = a … file 7 = h
```

`Square::E2` and `"e2".parse()` are the same value. `Square::all()` walks
this index order.

```text
8  a8  b8  c8  d8  e8  f8  g8  h8     56 57 58 59 60 61 62 63
7  a7  b7  c7  d7  e7  f7  g7  h7     48 49 50 51 52 53 54 55
6  a6  b6  c6  d6  e6  f6  g6  h6     40 41 42 43 44 45 46 47
5  a5  b5  c5  d5  e5  f5  g5  h5     32 33 34 35 36 37 38 39
4  a4  b4  c4  d4  e4  f4  g4  h4     24 25 26 27 28 29 30 31
3  a3  b3  c3  d3  e3  f3  g3  h3     16 17 18 19 20 21 22 23
2  a2  b2  c2  d2  e2  f2  g2  h2      8  9 10 11 12 13 14 15
1  a1  b1  c1  d1  e1  f1  g1  h1      0  1  2  3  4  5  6  7
    a   b   c   d   e   f   g   h
```

A Hall sensor at PCB index `12` is `Square::E2`. Do not invent a second
numbering scheme.

## Local play

```mermaid
sequenceDiagram
    participant App
    participant Game
    participant History
    participant Board

    App->>Game: Game::new() / from_board(board)
    Game->>History: anchor to initial board
    Game-->>App: Game

    App->>Game: play(e2e4)  or  piece.move_to(e4, game)
    Game->>Board: make canonical move
    alt legal
        Game->>History: append HistoryEvent::Move
        Game->>Game: finalize if mate / stalemate / auto-draw
        Game-->>App: Ok(HistoryStep)
    else illegal or blocked
        Game->>History: append HistoryEvent::Invalid
        Game-->>App: Err(MoveError)
    end
```

```rust
use chess::{ChessMove, Game, HistoryEvent, Square};

let mut game = Game::new();
let step = game.play(ChessMove::new(Square::E2, Square::E4))?;
assert!(matches!(step.event(), HistoryEvent::Move(_)));
# Ok::<(), chess::MoveError>(())
```

`play` returns the `HistoryStep` to persist or send. Queen is the default
promotion; `move_and_promote` selects any other kind.

`Game::legal_moves` is empty while history is invalid or final. Light LEDs from
the `Game`, not from a copied `Board` that cannot see an unresolved error.

## Observation

Read paths borrow. They do not clone the aggregate.

```mermaid
flowchart LR
    G["Game borrow"]
    G --> B["board() / piece_at()"]
    G --> P["pieces() / iterate Game"]
    G --> S["status()"]
    G --> H["history()"]
    G --> D["draw_claims()"]
    G --> I["latest_invalid()"]
    G --> C["side_to_move() / is_in_check()"]
```

```mermaid
stateDiagram-v2
    [*] --> InProgress: Game::new()
    InProgress --> DrawClaimAvailable: threefold / fifty-move
    DrawClaimAvailable --> InProgress: claim not taken, play continues
    InProgress --> Invalid: rejected play / sync / claim
    DrawClaimAvailable --> Invalid: rejected claim
    Invalid --> InProgress: resolve_latest_invalid
    Invalid --> Invalid: another invalid
    InProgress --> Checkmate: no legal move, in check
    InProgress --> Stalemate: no legal move, not in check
    InProgress --> Draw: auto-draw or claim
    DrawClaimAvailable --> Draw: claim_draw
    Checkmate --> [*]
    Stalemate --> [*]
    Draw --> [*]
```

`status().is_terminal()` is the UI flag for “accept no further legal play.”
Menu code borrows `&Game` while firmware keeps mutable hardware state
elsewhere.

## Invalid operations

Rejected play is retained. The board cache does not change.

```mermaid
stateDiagram-v2
    [*] --> Active: empty or latest Move
    Active --> Active: Move
    Active --> Invalid: Invalid
    Active --> Final: Final
    Invalid --> Invalid: Invalid
    Invalid --> Active: resolve_latest_invalid
    Final --> [*]
```

Resolution is a stack. Newest invalid comes off first. A valid move cannot be
spliced underneath.

```text
tip ──► Invalid  PendingInvalid     ◄── resolve_latest_invalid
        Invalid  WrongSide          ◄── then this
        Move     e2e4
        ────────────────────────
        Final seals the timeline. Nothing follows.
```

| Latest event | `play` | `accept` Move/Final | `resolve_latest_invalid` |
|---|---|---|---|
| none / Move | apply or record Invalid | allowed if legal | error |
| Invalid | record `PendingInvalid` | Move/Final refused | pops newest |
| Final | `GameOver` | refused | error |

## Draws

```mermaid
flowchart TB
    POS["current position"]
    POS --> MATE{"no legal move?"}
    MATE -->|in check| CM["Final Checkmate"]
    MATE -->|not in check| ST["Final Stalemate"]
    MATE -->|legal moves remain| AUTO{"automatic draw?"}
    AUTO -->|insufficient / fivefold / 75-move| AD["Final Draw"]
    AUTO -->|no| CLAIM{"claim available?"}
    CLAIM -->|threefold / 50-move| DC["DrawClaimAvailable"]
    CLAIM -->|no| IP["InProgress"]
    DC -->|"claim_draw / claim_draw_after"| CD["Final Draw"]
```

| Situation | Consumer action |
|---|---|
| Threefold or fifty-move | `draw_claims()` then `claim_draw` |
| Claim after an announced legal move | `draw_claims_after(m)` then `claim_draw_after(m, claim)` |
| Fivefold, seventy-five-move, insufficient material | none — already finalized |
| Checkmate or stalemate | none — those outrank remaining claims |

`claim_draw_after` keeps the announced move as evidence and **does not play
it**. The game ends immediately.

Repetition identity:

```text
┌───────────┬──────────────┬──────────┬─────────────────────────┐
│ placement │ side to move │ castling │ en passant if capture   │
│           │              │ rights   │ is actually legal       │
└───────────┴──────────────┴──────────┴─────────────────────────┘
 halfmove / fullmove clocks are not in this key
```

## Synchronization and persistence

The value that leaves the process is `HistoryStep`. It is `Copy`.

```text
┌──────┬──────────────────────┬──────────────┬──────────────┐
│ ply  │ event                │ previous     │ hash         │
│  1   │ Move e2e4            │ board anchor │ SHA-256      │
│  2   │ Move e7e5            │ hash 1       │ SHA-256      │
│  3   │ Invalid WrongSide    │ hash 2       │ SHA-256      │
│  4   │ Final Checkmate      │ hash 3       │ SHA-256      │
└──────┴──────────────────────┴──────────────┴──────────────┘
 anchor ──► step ──► step ──► step ──► tip
```

```mermaid
sequenceDiagram
    participant Store
    participant Peer
    participant Game
    participant History

    Peer->>Game: accept(step)
    Game->>History: sequence, previous hash, event hash
    alt hashes and chess both valid
        Game->>Game: update board cache, maybe auto-final
        Game-->>Peer: Ok
    else divergence
        Game->>History: Invalid Synchronization
        Game-->>Peer: Err(GameSyncError)
    end

    Store->>Game: load steps, accept each
    Store->>Game: verify()
    Game->>History: recompute chain
    Game->>Game: replay moves from initial board
    Game-->>Store: Ok or GameVerificationError
```

| API | Checks hashes | Checks chess | Updates `Game` board |
|---|---|---|---|
| `Game::accept` | yes | yes | yes |
| `GameHistory::try_append` | yes | **no** | no |
| `Game::play` / `claim_draw` | yes | yes | yes |

Application code playing chess calls `play`, `claim_draw`, `accept`, or
`resolve_latest_invalid`. Do not assemble events by hand and
`try_append` them onto a live game.

The hash chain detects corruption and divergence. It does not authenticate a
peer.

## Setup and the physical board

`Game` has no API for “the sensors look wrong.” Invalid events on a live match
are produced only by `play`, `claim_draw` / `claim_draw_after`, and `accept`.
`history()` is read-only. Firmware owns occupancy that is not yet a chess
operation.

```mermaid
flowchart TB
    SENSORS["64 Hall sensors"] -->|"index = SquareIndex"| SQ["Square"]
    SQ --> PHYS["physical occupancy"]
    PHYS --> CMP{"compare to game.board()"}
    CMP -->|"completed displacement is a ChessMove"| PLAY["game.play / piece.move_to"]
    PLAY -->|"legal"| MOVE["HistoryEvent::Move"]
    PLAY -->|"illegal"| INV["HistoryEvent::Invalid Move"]
    CMP -->|"lifted, hovering, extra trip, debounce"| ADAPTER["adapter-local state"]
    SETUP["Board::from_pieces / force_move"] -->|"then"| FROM["Game::from_board"]
```

```rust
use chess::{Board, Color, Game, Piece, PieceKind, Square};

let mut board = Board::from_pieces([
    Piece::new(Color::White, PieceKind::King, Square::E1),
    Piece::new(Color::Black, PieceKind::King, Square::E8),
]);
board.set_side_to_move(Color::White);
let game = Game::from_board(board);
```

`Board::force_move` relocates without rules, clocks, castling, en passant, or
history. Use it to assemble a snapshot, then wrap with `Game::from_board`.
It is not a back door into a live `Game`. There is no FEN parser here.

## Logging

Optional sidecar. The API is the `HistoryStep`, not the log line.

```mermaid
flowchart LR
    APP["application startup"] -->|"register once"| L["logger singleton"]
    G["Game"] -.->|"target chess::game"| L
    L --> SYS["systemd / stderr / test sink"]
```

Hosted backends live behind the logger crate's `std` feature. The chess crate
does not enable it:

```toml
logger = { path = "../logger", features = ["std"] }
```

```rust
use logger::{LevelFilter, implementations::SystemdLogger, register};

static LOGGER: SystemdLogger = SystemdLogger::new(LevelFilter::Info);
register(&LOGGER)?;
# Ok::<(), logger::RegistrationError>(())
```

Without `std`, implement `Logger` yourself and register that. `NopLogger` is
always available. No registration → complete silence.

| Event | Level |
|---|---|
| created | debug |
| move, resolution, final | info |
| invalid | warn |

## What stays outside

```text
┌──────────────────────────────────────────────┐
│  chess                                       │
│  rules · values · Game · hash-linked history │
└──────────────────────────────────────────────┘
        ▲
        │  crate root only
┌───────┴──────────────────────────────────────┐
│  firmware   simulator   persistence   net    │
│  GPIO I²C SPI OLED buttons debounce          │
│  SAN PGN FEN UCI  clocks  matchmaking        │
│  files SQLite  auth  search  async           │
└──────────────────────────────────────────────┘
```

`Board::legal_moves` is a rules query, not a search API.

## Hash encodings

Public contract. Private functions. Integers below are the on-wire tags.
Domains include a trailing `NUL`. Do not hash `Debug` output.

```text
event hash = SHA-256
┌──────────────────────────────────────────────┐
│ b"chess.game-history.sha256.v1\0"   29 bytes │
│ previous hash                       32 bytes │
│ ply as big-endian u64                8 bytes │
│ event payload                         varies │
└──────────────────────────────────────────────┘

board anchor = SHA-256
┌──────────────────────────────────────────────┐
│ b"chess.board-anchor.sha256.v1\0"   29 bytes │
│ 64 occupancy bytes, a1 → h8          64 bytes │
│ side to move                          1 byte │
│ WK WQ BK BQ, each 0 or 1              4 bytes │
│ en passant: index, or 0xFF            1 byte │
│ halfmove clock, big-endian u32        4 bytes │
│ fullmove number, big-endian u32       4 bytes │
└──────────────────────────────────────────────┘
```

Occupancy byte: `0` empty, otherwise `color × 6 + kind + 1`.

| | White `0` | Black `1` |
|---|---|---|
| Pawn `0` | `1` | `7` |
| Knight `1` | `2` | `8` |
| Bishop `2` | `3` | `9` |
| Rook `3` | `4` | `10` |
| Queen `4` | `5` | `11` |
| King `5` | `6` | `12` |

Move promotion byte: none `0`, Knight `1`, Bishop `2`, Rook `3`, Queen `4`.

| Event | First byte | Then |
|---|---|---|
| `Move` | `0` | `from`, `to`, promotion |
| `Invalid` | `1` | invalid tag |
| `Final` | `2` | final tag |

| Invalid | Tag | Then |
|---|---|---|
| `Move` | `0` | move-error tag |
| `Synchronization` | `1` | sync-error tag |
| `DrawClaim` | `2` | claim tag |
| `PendingInvalid` | `3` | — |

| Final | Tag | Then |
|---|---|---|
| `Checkmate` | `0` | winner color |
| `Stalemate` | `1` | — |
| `Draw` | `2` | draw-reason tag |
| `DrawAfter` | `3` | claim tag, then move `from`/`to`/promotion |

| Draw claim | | Draw reason | |
|---|---|---|---|
| Threefold | `0` | Claimed | `0` + claim |
| Fifty-move | `1` | Insufficient material | `1` |
| | | Fivefold | `2` |
| | | Seventy-five-move | `3` |

| `MoveError` | Tag | Then |
|---|---|---|
| `GameOver` | `0` | final payload |
| `PendingInvalid` | `1` | — |
| `NoPiece` | `2` | square index |
| `WrongSide` | `3` | expected color, actual color |
| `IllegalDestination` | `4` | from index, to index |
| `UnexpectedPromotion` | `5` | — |
| `InvalidPromotion` | `6` | — |
| `NonCanonicalPromotion` | `7` | — |
| `StalePiece` | `8` | — |

| `GameSyncError` | Tag | Then |
|---|---|---|
| `History` | `0` | history-error tag |
| `Move` | `1` | move-error payload |

| `HistoryError` | Tag | Then |
|---|---|---|
| `Ply` | `0` | expected u64 BE, actual u64 BE |
| `PreviousHash` | `1` | ply u64 BE, expected 32, actual 32 |
| `Hash` | `2` | ply u64 BE, expected 32, actual 32 |
| `InvalidTransition` | `3` | optional current kind, incoming kind |
| `NothingToResolve` | `4` | optional current kind |
| `Tip` | `5` | expected 32, actual 32 |

Optional event kind: `0` = none; `1` then kind. Kind: `Move 0`, `Invalid 1`,
`Final 2`.

Locked vector, unanchored history (`GameHistory::new()`, previous =
`HistoryHash::GENESIS`):

```text
Move e2e4 at ply 1
→ 59c8f0c8e610d5d3f71e08c7d6f8749bb8759167e8208c8c144f36650a44d5e6
```

`Game::new()` is not this vector: it anchors to `Board::INITIAL`, so the first
previous hash is the board-anchor digest, not genesis. Equal move lists from
different initial boards must not synchronize. Breaking a tag breaks every
stored and in-flight `HistoryStep`.

## Source layout

Internal map: [`src/README.md`](src/README.md). External rule:

```text
import from chess

  live match     →  Game
  leaves process →  HistoryStep
  describes a position →  Board / Piece / Square
```
