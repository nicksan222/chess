use firmware::events::Bus;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum TestEvent {
    SensorReading(u8),
    Stopped,
}

#[test]
fn callers_can_define_their_own_typed_events() {
    let bus = Bus::<TestEvent>::with_capacity(4);
    let mut subscription = bus.subscribe();

    bus.emit(TestEvent::SensorReading(42)).unwrap();
    bus.emit(TestEvent::Stopped).unwrap();

    assert_eq!(
        subscription.try_recv(),
        Ok(Some(TestEvent::SensorReading(42)))
    );
    assert_eq!(subscription.try_recv(), Ok(Some(TestEvent::Stopped)));
}
