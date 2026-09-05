#![allow(dead_code)]

#[path = "../src/pins/mod.rs"]
mod pins;

use std::collections::HashSet;

use pins::{
    BoardPins, Capability, CapabilityKind, Gpio, InputOutput, Level, OutputBackend, Pin, Readable,
    Writable,
};

#[derive(Default)]
struct FakeOutput {
    writes: Vec<(Gpio, Level)>,
}

impl OutputBackend for FakeOutput {
    type Error = ();

    fn set_level(&mut self, gpio: Gpio, level: Level) -> Result<(), Self::Error> {
        self.writes.push((gpio, level));
        Ok(())
    }
}

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
fn writable_pins_expose_electrical_and_logical_output_actions() {
    let pins = BoardPins::new();
    let mut backend = FakeOutput::default();

    pins.led_data.set_high(&mut backend).unwrap();
    pins.led_data.set_low(&mut backend).unwrap();
    pins.led_data.turn_on(&mut backend).unwrap();
    pins.led_data.turn_off(&mut backend).unwrap();
    pins.i2c_data.set_high(&mut backend).unwrap();

    assert_eq!(
        backend.writes,
        [
            (Gpio::LedData, Level::High),
            (Gpio::LedData, Level::Low),
            (Gpio::LedData, Level::High),
            (Gpio::LedData, Level::Low),
            (Gpio::I2cData, Level::High),
        ]
    );
}

#[test]
fn every_connected_gpio_has_a_unique_identity_and_meaningful_name() {
    assert_eq!(Gpio::ALL.len(), 16);

    let bcm_numbers: HashSet<_> = Gpio::ALL.iter().map(|gpio| gpio.bcm_number()).collect();
    let header_pins: HashSet<_> = Gpio::ALL.iter().map(|gpio| gpio.header_pin()).collect();
    let names: HashSet<_> = Gpio::ALL.iter().map(|gpio| gpio.name()).collect();

    assert_eq!(bcm_numbers.len(), Gpio::ALL.len());
    assert_eq!(header_pins.len(), Gpio::ALL.len());
    assert_eq!(names.len(), Gpio::ALL.len());
    assert!(
        Gpio::ALL
            .iter()
            .all(|gpio| !gpio.name().starts_with("GPIO"))
    );
}

#[test]
fn panel_buttons_are_active_low_inputs() {
    assert_eq!(Gpio::BUTTONS.len(), 12);
    assert!(Gpio::BUTTONS.contains(&Gpio::ResetButton));
    assert!(Gpio::BUTTONS.iter().all(|button| button.can_read()));
    assert!(Gpio::BUTTONS.iter().all(|button| !button.can_write()));
    assert!(Gpio::BUTTONS.iter().all(|button| button.is_active_low()));
}
