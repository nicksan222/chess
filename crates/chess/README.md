# Chess domain crate

This crate owns integration-neutral chess-domain logic. It provides strongly
typed board values, self-locating pieces, legal move generation, complete game
state, and SHA-256-linked move history. Board values and move rules are
allocation-free; move history intentionally uses `chess-core`'s safe
linked list. The crate does not own hardware, transport, or application
integration.
