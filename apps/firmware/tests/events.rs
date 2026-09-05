#![allow(dead_code, unused_imports)]

#[path = "../src/events/mod.rs"]
mod events;
#[path = "../src/pins/mod.rs"]
mod pins;

use std::io::ErrorKind;

use events::{Event, EventEmitter, GPIOLevelEvent, I2CEvent, I2COperation, ReceiveError, SPIEvent};
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
fn every_subscription_receives_events_from_every_emitter_in_order() {
    let pins = BoardPins::get();
    let emitter = EventEmitter::new(3);
    let other_emitter = emitter.clone();
    let mut first = emitter.subscribe();
    let mut second = emitter.subscribe();
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

    emitter.emit(gpio.clone()).unwrap();
    other_emitter.emit(i2c.clone()).unwrap();
    emitter.emit(spi.clone()).unwrap();

    for subscription in [&mut first, &mut second] {
        assert_eq!(subscription.try_recv(), Ok(Some(gpio.clone())));
        assert_eq!(subscription.try_recv(), Ok(Some(i2c.clone())));
        assert_eq!(subscription.try_recv(), Ok(Some(spi.clone())));
        assert_eq!(subscription.try_recv(), Ok(None));
    }
}

#[test]
fn emitter_accepts_typed_events_without_manual_erasure() {
    let pins = BoardPins::get();
    let emitter = EventEmitter::new(1);
    let mut subscription = emitter.subscribe();
    let event = GPIOLevelEvent::new(pins.gpio.ok_button.gpio(), Level::Low);

    emitter.emit(event).unwrap();

    assert_eq!(subscription.try_recv(), Ok(Some(Event::GPIOLevel(event))));
}

#[test]
fn subscriptions_report_lag_without_exposing_channel_errors() {
    let pins = BoardPins::get();
    let emitter = EventEmitter::new(1);
    let mut subscription = emitter.subscribe();

    emitter
        .emit(GPIOLevelEvent::new(
            pins.gpio.reset_button.gpio(),
            Level::Low,
        ))
        .unwrap();
    emitter
        .emit(GPIOLevelEvent::new(
            pins.gpio.reset_button.gpio(),
            Level::High,
        ))
        .unwrap();

    assert_eq!(
        subscription.try_recv(),
        Err(ReceiveError::Lagged { skipped: 1 })
    );
    assert!(matches!(
        subscription.try_recv(),
        Ok(Some(Event::GPIOLevel(_)))
    ));
}

#[test]
fn failed_emission_returns_ownership_of_the_event() {
    let pins = BoardPins::get();
    let emitter = EventEmitter::new(1);
    let event = Event::from(GPIOLevelEvent::new(
        pins.gpio.reset_button.gpio(),
        Level::High,
    ));

    let returned = emitter.emit(event.clone()).unwrap_err().into_event();

    assert_eq!(returned, event);
    assert_eq!(emitter.subscriber_count(), 0);
}
