#![allow(dead_code)]

#[path = "../src/generated_pins.rs"]
mod generated_pins;

use generated_pins::{Gpio2, Gpio4, Gpio24, RaspberryPiPin};

#[test]
fn generated_markers_preserve_host_pin_identity() {
    assert_eq!(Gpio2::BCM_NUMBER, 2);
    assert_eq!(Gpio2::HEADER_PIN, 3);
    assert_eq!(Gpio4::BCM_NUMBER, 4);
    assert_eq!(Gpio4::HEADER_PIN, 7);
    assert_eq!(Gpio24::BCM_NUMBER, 24);
    assert_eq!(Gpio24::HEADER_PIN, 18);
}

#[test]
fn pin_markers_are_distinct_consumer_types() {
    fn bcm<P: RaspberryPiPin>(_: P) -> u8 {
        P::BCM_NUMBER
    }

    assert_eq!(bcm(Gpio2), 2);
    assert_eq!(bcm(Gpio4), 4);
}
