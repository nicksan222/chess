use chess_core::{Percentage, Toggle};

#[test]
fn toggle_is_explicit_and_reversible() {
    let mut toggle = Toggle::default();
    assert!(toggle.is_off());
    assert!(!bool::from(toggle));

    toggle.toggle();
    assert_eq!(toggle, Toggle::On);
    assert!(toggle.is_on());
    assert_eq!(toggle.toggled(), Toggle::Off);
    assert_eq!(Toggle::from(true), Toggle::On);
}

#[test]
fn percentage_enforces_its_range() {
    assert_eq!(Percentage::new(0), Ok(Percentage::ZERO));
    assert_eq!(Percentage::new(100), Ok(Percentage::FULL));
    assert_eq!(u8::from(Percentage::new(42).expect("valid")), 42);

    let error = Percentage::new(101).expect_err("out of range");
    assert_eq!(error.value(), 101);
    assert_eq!(error.to_string(), "percentage 101 is outside 0..=100");
}
