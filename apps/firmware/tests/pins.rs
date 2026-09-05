#![allow(dead_code)]

#[path = "../src/pins.rs"]
mod pins;

use std::collections::HashSet;

use pins::{ALL, BUTTONS, Capability, I2C_DATA, LED_DATA, RESET_BUTTON, UP_BUTTON};

#[test]
fn gpio_descriptors_expose_identity_and_capabilities() {
    assert_eq!(I2C_DATA.name(), "I2C data");
    assert_eq!(I2C_DATA.bcm_number(), 2);
    assert_eq!(I2C_DATA.header_pin(), 3);
    assert_eq!(I2C_DATA.capability(), Capability::InputOutput);
    assert!(I2C_DATA.can_read());
    assert!(I2C_DATA.can_write());

    assert_eq!(LED_DATA.bcm_number(), 10);
    assert!(!LED_DATA.can_read());
    assert!(LED_DATA.can_write());

    assert_eq!(UP_BUTTON.bcm_number(), 5);
    assert!(UP_BUTTON.can_read());
    assert!(!UP_BUTTON.can_write());
    assert!(UP_BUTTON.is_active_low());
}

#[test]
fn every_connected_gpio_has_a_unique_identity_and_meaningful_name() {
    assert_eq!(ALL.len(), 16);

    let bcm_numbers: HashSet<_> = ALL.iter().map(|gpio| gpio.bcm_number()).collect();
    let header_pins: HashSet<_> = ALL.iter().map(|gpio| gpio.header_pin()).collect();
    let names: HashSet<_> = ALL.iter().map(|gpio| gpio.name()).collect();

    assert_eq!(bcm_numbers.len(), ALL.len());
    assert_eq!(header_pins.len(), ALL.len());
    assert_eq!(names.len(), ALL.len());
    assert!(ALL.iter().all(|gpio| !gpio.name().starts_with("GPIO")));
}

#[test]
fn panel_buttons_are_active_low_inputs() {
    assert_eq!(BUTTONS.len(), 12);
    assert!(BUTTONS.contains(&RESET_BUTTON));
    assert!(BUTTONS.iter().all(|button| button.can_read()));
    assert!(BUTTONS.iter().all(|button| !button.can_write()));
    assert!(BUTTONS.iter().all(|button| button.is_active_low()));
}
