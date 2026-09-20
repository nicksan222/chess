use firmware::events::{Bus, ReceiveError};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum TestEvent {
    First,
    Second,
}

#[test]
fn every_subscription_receives_events_from_every_emitter_in_order() {
    let emitter = Bus::new();
    let other_emitter = emitter.clone();
    let mut first = emitter.subscribe();
    let mut second = emitter.subscribe();

    emitter.emit(TestEvent::First).unwrap();
    other_emitter.emit(TestEvent::Second).unwrap();

    for subscription in [&mut first, &mut second] {
        assert_eq!(subscription.try_recv(), Ok(Some(TestEvent::First)));
        assert_eq!(subscription.try_recv(), Ok(Some(TestEvent::Second)));
        assert_eq!(subscription.try_recv(), Ok(None));
    }
}

#[test]
fn subscriptions_report_lag_without_exposing_channel_errors() {
    let emitter = Bus::new();
    let mut subscription = emitter.subscribe();

    for _ in 0..65 {
        emitter.emit(TestEvent::First).unwrap();
    }

    assert_eq!(subscription.try_recv(), Err(ReceiveError::Lagged(1)));
}

#[test]
fn failed_emission_returns_ownership_of_the_event() {
    let emitter = Bus::new();

    let returned = emitter.emit(TestEvent::First).unwrap_err().into_event();

    assert_eq!(returned, TestEvent::First);
    assert_eq!(emitter.subscriber_count(), 0);
}
