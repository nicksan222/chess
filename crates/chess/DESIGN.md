# Chess crate design

An application manages a match by holding one `Game`. Firmware, the simulator,
and tests all do the same thing: create a game, let the side to move play, and
read `status()` until it is over.

This crate does not have players. It has **two sides**.

```text
        your app owns people, seats, clocks, online identity
                         │
                         v
              ┌─────────────────────┐
              │        Game         │
              │                     │
   White ───► │  side_to_move()     │
   Black ───► │  play / claim       │
              │  status()           │
              └──────────┬──────────┘
                         │
                    HistoryStep
                  persist / send
```

## Players are colors

```text
Color::White     moves first
Color::Black     moves second
Color::ALL       [White, Black]
color.opposite() the other side
```

A piece belongs to a color. The winner of checkmate is a color. Whose turn it
is is a color:

```rust
use chess::{Color, Game};

let game = Game::new();
assert_eq!(game.side_to_move(), Color::White);
```

Map real people onto those two values in the application:

| Product situation | White | Black |
|---|---|---|
| 1 vs 1 at the board | near side | far side |
| 1 vs online | local player | peer, or the reverse |
| tests / bots | whoever you say | whoever you say |

Names, accounts, who sits where, and chess clocks stay outside this crate.

## Start

```rust
use chess::Game;

let mut game = Game::new();              // standard starting position
let mut game = Game::from_board(board);  // or a position you assembled
```

White is to move unless the board says otherwise.

## The side to move plays

Ask the game whose turn it is. Only that color may move.

```rust
use chess::{ChessMove, Color, Game, Square};

let mut game = Game::new();
assert_eq!(game.side_to_move(), Color::White);

game.play(ChessMove::new(Square::E2, Square::E4))?;
assert_eq!(game.side_to_move(), Color::Black);
```

Same move, said from the piece the player touched:

```rust
let pawn = game.piece_at(Square::E2).unwrap();
pawn.move_to(Square::E4, &mut game)?;
```

If it is White's turn and Black's piece moves, `play` returns
`MoveError::WrongSide` and records an invalid event. The board does not
change. Resolve it, then the same player tries again:

```rust
game.resolve_latest_invalid()?;
```

Pawns to the back rank become a queen unless the player picks another kind
with `move_and_promote`.

## Look at the match

```text
game.side_to_move()     whose turn
game.board()            the position
game.piece_at(square)   what occupies a square
game.pieces()           every piece, with its color
game.legal_moves()      what the side to move may play
game.status()           in progress, claim, invalid, or over
game.history()          the official timeline
```

Light legal squares from `game.legal_moves()`, not from a copied board.
`legal_moves` is empty while the game is invalid or finished.

```text
status()
  InProgress              play
  DrawClaimAvailable      play, or the side to move claims
  Invalid                 resolve_latest_invalid, then continue
  Checkmate { winner }    over — winner is a Color
  Stalemate               over
  Draw { reason }         over
```

`status().is_terminal()` means no more legal play.

The side to move may claim threefold repetition or the fifty-move rule with
`claim_draw`. Announcing a move that would make a claim available uses
`claim_draw_after` — the move is evidence, it is not played. Automatic draws
and mate are applied by `play` itself.

## Two games talking

Each side of an online match holds its own `Game`. A local `play` returns a
`HistoryStep`. The other process applies it with `accept`. After load, call
`verify()`.

```text
player A:  game.play(move)  ──HistoryStep──►  player B: game.accept(step)
```

Authentication, seating ("you are Black"), and the network are the
application.

## What the application owns

```text
this crate                         the application
─────────────────────────          ─────────────────────────
Game, Color, pieces, rules         who White and Black are
legal play and game status         buttons, LEDs, OLED
HistoryStep                        files, SQLite, sockets
                                   clocks, names, matchmaking
```
