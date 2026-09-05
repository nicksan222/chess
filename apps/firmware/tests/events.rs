#![allow(dead_code, unused_imports)]

#[path = "../src/events/mod.rs"]
mod events;
#[path = "../src/pins/mod.rs"]
mod pins;

use std::io::ErrorKind;

use events::{Event, GPIOLevelEvent, I2CEvent, I2COperation, SPIEvent};
use pins::{BoardPins, Level};

#[test]
fn gpio_events_identify_any_pin_and_its_electrical_level() {
    let pins = BoardPins::get();
    let button = GPIOLevelEvent::new(pins.gpio.ok_button.gpio(), Level::Low);
    let i2c = GPIOLevelEvent::new(pins.i2c.data.gpio(), Level::High);
    let spi = GPIOLevelEvent::new(pins.spi.clock.gpio(), Level::Low);

    assert_eq!(button.gpio().bcm_number(), 16);
    assert_eq!(button.level(), Level::Low);
    assert_eq!(i2c.gpio().bcm_number(), 2);
    assert_eq!(spi.gpio().bcm_number(), 11);
}

#[test]
fn i2c_events_capture_logical_operations_and_results() {
    let read = I2CEvent::new(
        0x20,
        I2COperation::WriteRead {
            written: vec![0x00],
            read: vec![0b1010_0101],
        },
        Ok(()),
    );
    let failed = I2CEvent::new(
        0x3c,
        I2COperation::Write { bytes: vec![0xae] },
        Err(ErrorKind::TimedOut),
    );

    assert_eq!(read.address(), 0x20);
    assert_eq!(
        read.operation(),
        &I2COperation::WriteRead {
            written: vec![0x00],
            read: vec![0b1010_0101]
        }
    );
    assert_eq!(read.result(), &Ok(()));
    assert_eq!(failed.address(), 0x3c);
    assert_eq!(failed.result(), &Err(ErrorKind::TimedOut));
}

#[test]
fn spi_events_capture_output_only_led_writes() {
    let event = SPIEvent::new(vec![0x00, 0x00, 0x00, 0x00], Ok(()));

    assert_eq!(event.bytes(), [0x00, 0x00, 0x00, 0x00]);
    assert_eq!(event.result(), &Ok(()));
}

#[test]
fn bounded_channel_delivers_mixed_interface_events_in_order() {
    let pins = BoardPins::get();
    let (sender, mut receiver) = events::channel(3);
    let gpio = Event::from(GPIOLevelEvent::new(
        pins.gpio.reset_button.gpio(),
        Level::Low,
    ));
    let i2c = Event::from(I2CEvent::new(
        0x20,
        I2COperation::Read { bytes: vec![0xff] },
        Ok(()),
    ));
    let spi = Event::from(SPIEvent::new(vec![0; 4], Err(ErrorKind::BrokenPipe)));

    sender.try_send(gpio.clone()).unwrap();
    sender.try_send(i2c.clone()).unwrap();
    sender.try_send(spi.clone()).unwrap();

    assert_eq!(receiver.try_recv(), Ok(gpio));
    assert_eq!(receiver.try_recv(), Ok(i2c));
    assert_eq!(receiver.try_recv(), Ok(spi));
}

#[test]
fn bounded_channel_reports_backpressure() {
    let pins = BoardPins::get();
    let (sender, _receiver) = events::channel(1);

    sender
        .try_send(Event::from(GPIOLevelEvent::new(
            pins.gpio.reset_button.gpio(),
            Level::Low,
        )))
        .unwrap();

    assert!(
        sender
            .try_send(Event::from(GPIOLevelEvent::new(
                pins.gpio.reset_button.gpio(),
                Level::High,
            )))
            .is_err()
    );
}

#[test]
fn emitter_accepts_typed_events_without_manual_erasure() {
    let pins = BoardPins::get();
    let (emitter, mut receiver) = events::channel(1);
    let event = GPIOLevelEvent::new(pins.gpio.ok_button.gpio(), Level::Low);

    emitter.try_emit(event).unwrap();

    assert_eq!(receiver.try_recv(), Ok(Event::GPIOLevel(event)));
}

#[test]
fn failed_emission_returns_ownership_of_the_event() {
    let pins = BoardPins::get();
    let (emitter, receiver) = events::channel(1);
    let event = Event::from(GPIOLevelEvent::new(
        pins.gpio.reset_button.gpio(),
        Level::High,
    ));
    drop(receiver);

    let returned = emitter.try_emit(event.clone()).unwrap_err().into_inner();

    assert_eq!(returned, event);
    assert!(emitter.is_closed());
}
