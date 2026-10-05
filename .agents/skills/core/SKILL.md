---
name: core
description: The purpose and outside view of `chess-core`, the workspace's small shared vocabulary of collections and values. Use when reaching for a shared building block or deciding whether something new belongs in core.
---

# core (`chess-core`)

## What it is for

Core is the shared vocabulary of the workspace: a few plain building blocks
that more than one crate needs and none of them should own. It has no
opinions about chess, hardware or storage, and it has no dependencies.

It holds two kinds of things:

- **Collections** for constrained targets: growable ones (linked list, queue,
  stack) when an allocator exists, and fixed-capacity ones (ring buffer,
  array stack) when it doesn't.
- **Meaningful values** that are otherwise just numbers or booleans:
  `Percentage` can only ever hold `0..=100`, and `Toggle` says "on/off"
  instead of a bare `bool`.

## How it thinks

- **A value that exists is a valid value.** Invalid states should be
  impossible to build, not checked again later.
- **Fullness is explicit.** A fixed-capacity collection never drops data
  silently: you either get your element back or you deliberately choose to
  overwrite the oldest.
- **Earn your place.** Something enters core only when it has a real
  consumer today, clear invariants, and no tie to hardware or an
  application. Core is not a utility drawer.

## Using it from outside

- Prefer these types over raw primitives when the meaning matters, for
  example a brightness is a `Percentage`, not a `u8`.
- Use the fixed-capacity collections where allocation is unwelcome, and
  handle the "full" case on purpose.
- Remember that other crates rely on these types' meaning: chess keeps its
  history in the linked list, and persistence gives `Percentage` and
  `Toggle` stable stored forms.

## Where things belong

Chess rules go to `chess`, storage formats to `persistence`, and device
code to firmware. Core keeps only what is neutral and shared.
