#![allow(dead_code)]

#[path = "../src/generated_pins.rs"]
mod generated_pins;

use generated_pins::{Gpio2, Gpio3, Gpio24, RaspberryPiPin};

#[test]
fn generated_markers_preserve_host_pin_identity() {
    assert_eq!(Gpio2::BCM_NUMBER, 2);
    assert_eq!(Gpio2::HEADER_PIN, 3);
    assert_eq!(Gpio3::BCM_NUMBER, 3);
    assert_eq!(Gpio3::HEADER_PIN, 5);
    assert_eq!(Gpio24::BCM_NUMBER, 24);
    assert_eq!(Gpio24::HEADER_PIN, 18);
}

#[test]
fn pin_markers_are_distinct_consumer_types() {
    fn bcm<P: RaspberryPiPin>(_: P) -> u8 {
        P::BCM_NUMBER
    }

    assert_eq!(bcm(Gpio2), 2);
    assert_eq!(bcm(Gpio3), 3);
}
