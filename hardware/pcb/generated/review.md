# PCB review

D-PROTOTYPE: 327 components, 253 connections.

- components: unchanged
- nets: unchanged
- placements: unchanged
- rules: unchanged

## Checks
- Passed: generation
- Passed: ERC
- Passed: DRC and schematic parity
- Passed: unit and SPICE tests (145 tests; 4 of them bound known residuals, listed below)
- Passed: previews

## Known residuals

These tests pass while the board still fails in a recorded way: they bound
the residual so it cannot get worse; they do not show a correct behaviour.

- `spice.test_led_switch.LedSwitchSpiceTest.test_enable_into_a_lit_chain_is_the_recorded_residual`: ASSUMPTION "LED power-up state"
- `spice.test_power.EfuseSpiceTest.test_running_supply_step_reaches_the_rail_until_ovlo_trips`: ASSUMPTION "OVLO filter"
- `spice.test_power.EfuseSpiceTest.test_ovlo_restart_is_a_latch_off_at_normal_supplies`: ASSUMPTION "OVLO window"
- `spice.test_power.EfuseSpiceTest.test_reversed_wrong_adapter_exceeds_the_bias_pin_limit`: ASSUMPTION "Reversed 12 V adapter"

Physical evidence missing: hall-magnet.json.

Generation alone is not release approval.
