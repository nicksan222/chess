# Board model source

- `mapping.rs` — which expander pin reads a square, and where a square sits in
  the LED chain. Both must agree with `hardware/shared/wiring.py`.
- `occupancy.rs` — one bit per square, indexed as `chess::Square` indexes
  itself, plus the conversion from raw expander port bytes. The Hall-output-active-low
  inversion is handled there, once.
- `debounce.rs` — consecutive-agreement filtering, which is what lets the board
  omit hardware debounce components.

Types are added only after their semantics and ownership are deliberately
designed.
