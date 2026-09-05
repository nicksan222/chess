# SPICE tests

Each `test_*.py` is a complete, readable electrical scenario. It:

1. asks `BoardHarness` for circuit topology derived from the validated PCB;
2. declares actions and named voltage/current checks in Python;
3. writes a same-named `test_*.cir` beside itself;
4. runs that circuit with ngspice.

The generated circuit contains its own `.control` assertion harness. A failed
bound executes `quit 1`, so Python does not duplicate electrical assertions.

For example, movement cases read chronologically:

```python
case = (
    MovementCase("quiet")
    .starts_with("A2")
    .expect_occupied("origin_before_lift", "A2", at_ms=0.25)
    .expect_empty("target_before_move", "A4", at_ms=0.25)
    .lift("A2", at_ms=1)
    .expect_empty("origin_after_lift", "A2", at_ms=1.25)
    .place("A4", at_ms=2)
    .expect_occupied("target_after_place", "A4", at_ms=2.25)
)
```

Support modules are deliberately local to this test group:

- `movement.py` — chronological movement/check DSL;
- `circuit.py` — one-method-per-SPICE-row builder and ngspice runner;
- `board_harness.py` — conversion from real board components/nets to circuits;
- `support.py` — common board loading and colocated `.cir` output.
