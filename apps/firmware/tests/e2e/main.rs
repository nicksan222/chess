use firmware::{
    hardware::pins::{Button, ButtonEvent},
    harness::FirmwareHarness,
};

#[tokio::test]
async fn injected_buttons_drive_the_real_menu() {
    let mut firmware = FirmwareHarness::start().unwrap();
    assert_eq!(firmware.snapshot().processed_events, 0);

    let moved = firmware
        .trigger(ButtonEvent::Pressed(Button::Next))
        .await
        .unwrap();
    assert_eq!(moved.selected_index, 1);
    assert_eq!(moved.processed_events, 1);

    let released = firmware
        .trigger(ButtonEvent::Released(Button::Next))
        .await
        .unwrap();
    assert_eq!(released.selected_index, 1);
    assert_eq!(released.processed_events, 2);

    let previous = firmware
        .trigger(ButtonEvent::Pressed(Button::Previous))
        .await
        .unwrap();
    assert_eq!(previous.selected_index, 0);
    let opened = firmware
        .trigger(ButtonEvent::Pressed(Button::Confirm))
        .await
        .unwrap();
    assert_eq!(opened.menu_depth, 1);
    let closed = firmware
        .trigger(ButtonEvent::Pressed(Button::Back))
        .await
        .unwrap();
    assert_eq!(closed.menu_depth, 0);
    firmware.shutdown().await.unwrap();
}

#[tokio::test]
async fn firmware_instances_are_isolated_and_restart_cleanly() {
    let mut first = FirmwareHarness::start().unwrap();
    let second = FirmwareHarness::start().unwrap();
    first
        .trigger(ButtonEvent::Pressed(Button::Next))
        .await
        .unwrap();
    assert_eq!(second.snapshot().processed_events, 0);
    first.shutdown().await.unwrap();
    second.shutdown().await.unwrap();
    let restarted = FirmwareHarness::start().unwrap();
    assert_eq!(restarted.snapshot().selected_index, 0);
    restarted.shutdown().await.unwrap();
}

#[test]
fn starting_firmware_without_runtime_is_an_error() {
    assert!(FirmwareHarness::start().is_err());
}
