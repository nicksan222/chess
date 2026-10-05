---
name: chess
description: The purpose and outside view of the `chess` crate, the board's rules engine and keeper of game truth. Use when code needs to know what a move means, whether a game is over, or how to drive a game from outside the crate.
---

# chess

## What it is for

The chess crate answers one question: *what is true about this game?* It
knows the rules completely and nothing else. A physical board, a screen, a
network peer or a computer opponent all ask it the same question and get the
same answer.

It does not know that the board has magnets, LEDs or buttons. It does not
store, send or display anything. That ignorance is deliberate: the rules can
be tested, replayed and trusted without any hardware.

## How it thinks

- **History is the truth; the board is a view of it.** A game is a sealed,
  hash-linked chain of events. The current position is only what that chain
  implies. Two parties with the same chain agree on everything.
- **Mistakes are recorded, not hidden.** An illegal or unexpected action
  becomes an explicit invalid event that must be resolved before play goes
  on, which matches the physical world where a piece can be put on the wrong
  square.
- **An ending is permanent.** Once a game is final it accepts nothing more.
- **Claims and certainties are different things.** Some draws must be
  claimed by a player and others happen automatically. The engine reports
  the difference rather than choosing for the player.
- **Silence by default.** It logs only if the host has registered a logger.

## Using it from outside

- Start a `GameSession` with two `Player`s (human, computer or online) and
  feed it moves. Players see a read-only view; only the session changes the
  game.
- Ask the game, not your own copy of the board: legal moves, side to move,
  check and status all come from it.
- To sync or store a game, exchange history steps and let the receiving game
  accept and verify them. The hash chain detects divergence and corruption,
  but it does not authenticate anyone; identity is the caller's problem.
- Computer moves are computed on the calling thread, so call them from a
  context that can afford the wait.

## Where things belong

Sensor interpretation, rendering, storage and transport belong to the caller.
Only the rules of chess and the integrity of a game's history belong here.
