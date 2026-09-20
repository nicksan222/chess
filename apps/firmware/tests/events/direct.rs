use firmware::events::direct_channel;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum TestEvent {
    First,
    Second,
}

#[tokio::test]
async fn delivers_once_and_applies_backpressure() {
    let (sender, mut receiver) = direct_channel(1);
    sender.send(TestEvent::First).await.unwrap();

    let blocked_send = tokio::spawn(async move { sender.send(TestEvent::Second).await });
    tokio::task::yield_now().await;
    assert!(!blocked_send.is_finished());

    assert_eq!(receiver.recv().await, Some(TestEvent::First));
    blocked_send.await.unwrap().unwrap();
    assert_eq!(receiver.recv().await, Some(TestEvent::Second));
}
