use firmware::events::{Button, Event, EventEmitter, ReceiveError};

#[test]
fn every_subscription_receives_events_from_every_emitter_in_order() {
    let emitter = EventEmitter::new();
    let other_emitter = emitter.clone();
    let mut first = emitter.subscribe();
    let mut second = emitter.subscribe();
    let pressed = Event::ButtonPressed(Button::Next);
    let released = Event::ButtonReleased(Button::Next);

    emitter.emit(pressed).unwrap();
    other_emitter.emit(released).unwrap();

    for subscription in [&mut first, &mut second] {
        assert_eq!(subscription.try_recv(), Ok(Some(pressed)));
        assert_eq!(subscription.try_recv(), Ok(Some(released)));
        assert_eq!(subscription.try_recv(), Ok(None));
    }
}

#[test]
fn subscriptions_report_lag_without_exposing_channel_errors() {
    let emitter = EventEmitter::new();
    let mut subscription = emitter.subscribe();

    for _ in 0..65 {
        emitter
            .emit(Event::ButtonPressed(Button::Previous))
            .unwrap();
    }

    assert_eq!(
        subscription.try_recv(),
        Err(ReceiveError::Lagged { skipped: 1 })
    );
}

#[test]
fn failed_emission_returns_ownership_of_the_domain_event() {
    let emitter = EventEmitter::new();
    let event = Event::ButtonPressed(Button::Confirm);

    let returned = emitter.emit(event).unwrap_err().into_event();

    assert_eq!(returned, event);
    assert_eq!(emitter.subscriber_count(), 0);
}
