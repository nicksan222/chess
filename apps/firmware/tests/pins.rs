#![allow(dead_code)]

#[path = "../src/pins/mod.rs"]
mod pins;

use std::collections::HashSet;

use pins::{
    ALL, BUTTONS, BoardPins, Capability, CapabilityKind, Gpio, InputOutput, Pin, Readable, Writable,
};

#[test]
fn gpio_enum_exposes_board_metadata() {
    assert_eq!(Gpio::I2cData.name(), "I2C data");
    assert_eq!(Gpio::I2cData.bcm_number(), 2);
    assert_eq!(Gpio::I2cData.header_pin(), 3);
    assert_eq!(Gpio::I2cData.capability(), CapabilityKind::InputOutput);
    assert!(Gpio::I2cData.can_read());
    assert!(Gpio::I2cData.can_write());

    assert!(!Gpio::LedData.can_read());
    assert!(Gpio::LedData.can_write());
    assert!(Gpio::UpButton.is_active_low());
}

#[test]
fn pin_types_encode_line_and_capability() {
    fn capability<const BCM: u8, C: Capability>(_: &Pin<BCM, C>) -> CapabilityKind {
        C::KIND
    }

    fn read<const BCM: u8, C: Readable>(pin: &Pin<BCM, C>) -> u8 {
        pin.bcm_number()
    }

    fn write<const BCM: u8, C: Writable>(pin: &Pin<BCM, C>) -> u8 {
        pin.bcm_number()
    }

    fn i2c_data(pin: &Pin<2, InputOutput>) -> Gpio {
        pin.gpio()
    }

    let pins = BoardPins::new();

    assert_eq!(capability(&pins.up_button), CapabilityKind::Input);
    assert_eq!(read(&pins.up_button), 5);
    assert_eq!(read(&pins.i2c_data), 2);
    assert_eq!(write(&pins.led_data), 10);
    assert_eq!(write(&pins.i2c_data), 2);
    assert_eq!(i2c_data(&pins.i2c_data), Gpio::I2cData);
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
    assert!(BUTTONS.contains(&Gpio::ResetButton));
    assert!(BUTTONS.iter().all(|button| button.can_read()));
    assert!(BUTTONS.iter().all(|button| !button.can_write()));
    assert!(BUTTONS.iter().all(|button| button.is_active_low()));
}
