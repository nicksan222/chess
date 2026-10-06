# SPICE tests

Tests are grouped into power, signal and movement scenarios (plus a plane-drop
group). They are SPICE simulations of the generated design, not measurements of a
built board. Each scenario:

1. asks `BoardHarness` for circuit topology derived from the validated PCB;
2. declares actions and named voltage/current checks in Python;
3. renders a uniquely named `.cir` into the review output set (or a temporary directory for standalone tests);
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

What each group covers:

- `test_power.py`: the supply-to-board path at datasheet corners (`power_path.py`), with
  a behavioural TPS259474 eFuse (`efuse_model.py`, no vendor model): worst-corner rail
  at the Pi and every LED, inrush against the fuse's I²t, slow-start, the over-voltage
  window against the supply and wrong adapters, OVLO latch-off after a trip, hot-plug
  ring with the OVLO filter,
  a running supply step, reversed plug, rocker off, full white against the approved
  load, and the +5V/LED_5V/ground plane drop from `plane_mesh.py` (a smeared resistor mesh of
  the real zone fill, within a 50 mV budget). The eFuse's start-up limit, ITIMER breaker, fast trip
  and auto-retry are simulated (`efuse_model.py`); thermal shutdown is not.
- `test_signals.py`: each of the 12 buttons pulled alone from its pad geometry (the
  TL1105's internally connected lead pairs and dome), every square's Hall output
  reaching a valid GPIO level, both AHCT125 channels reaching valid LED logic levels,
  and the open-drain I2C buses.
- `test_led_switch.py` (with `led_switch_model.py`): the LED rail switch Q1/Q2. A
  chain that powers up lit stays off until `LED_EN` rises, enabling a blanked chain keeps
  the input under the eFuse limit, and enabling into a lit chain is recorded as a
  residual, not a pass. Full white and a lit chain at enable trip the eFuse at both
  overcurrent branches with the fuse's I²t inside the 20 % pulse rule; U5's outputs stay
  within 0.3 V of the LED rail through enable and disable and within 0.3 V of ground while
  off (R17/R18).
- `test_i2c.py`: I²C bus capacitance, rise time and sink current at the firmware rate
  over the OLED pull-up corners (only 100 kHz passes); `test_led_lines.py`: AHCT125 to
  LED and LED-to-LED line edges at the supply corners, against SK9822 input limits, plus a per-pair data/clock setup check at the 10 MHz
  contract clock.
- `test_movement.py`: lift and place, capture, king-and-rook, three-square and promotion-rank
  transitions are visible electrically.

Support modules are deliberately local to this test group:

- `movement.py` — chronological movement/check DSL;
- `circuit.py` — minimal SPICE rendering and ngspice runner;
- `board_harness.py` — conversion from real board components/nets to circuits;
- `support.py` — common board loading and optional staged `.cir` output;
- `datasheets.py` — device internals and limits, each with its manufacturer source;
- `plane_mesh.py` — the plane resistor mesh used by the plane-drop tests;
- `electrical.py` — shared electrical limits for the checks;
- `led_switch_model.py` — SPICE rows for the LED rail switch.
