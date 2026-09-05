use super::*;

#[test]
fn bounce_and_held_levels_emit_only_stable_edges() {
    let start = Instant::now();
    let mut button = Debouncer::new(Level::High);
    assert_eq!(button.observe(Level::Low, start), None);
    assert_eq!(button.observe(Level::High, start + POLL_INTERVAL), None);
    assert_eq!(button.observe(Level::Low, start + DEBOUNCE), None);
    assert_eq!(
        button.observe(Level::Low, start + DEBOUNCE * 2),
        Some(ButtonAction::Pressed)
    );
    assert_eq!(button.observe(Level::Low, start + DEBOUNCE * 3), None);
    assert_eq!(button.observe(Level::High, start + DEBOUNCE * 4), None);
    assert_eq!(
        button.observe(Level::High, start + DEBOUNCE * 5),
        Some(ButtonAction::Released)
    );
}

#[test]
fn read_failure_restarts_debounce_without_losing_last_stable_level() {
    let start = Instant::now();
    let mut button = Debouncer::new(Level::Low);
    assert_eq!(button.observe(Level::High, start), None);
    button.interrupt();
    assert_eq!(button.observe(Level::High, start + DEBOUNCE), None);
    assert_eq!(
        button.observe(Level::High, start + DEBOUNCE * 2),
        Some(ButtonAction::Released)
    );
}

#[test]
fn initial_level_is_a_baseline_not_a_synthetic_press() {
    let mut button = Debouncer::new(Level::Low);
    assert_eq!(button.observe(Level::Low, Instant::now()), None);
}
