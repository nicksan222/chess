mod connectivity;
mod gpio;
mod linux;
mod probe_case;
mod vm;
mod wifi;

use firmware::{
    hardware::{
        BoardPosition, HardwareEvent, PieceEvent,
        pins::{Button, ButtonEvent},
    },
    harness::FirmwareHarness,
    menu::Request,
    runtime::Snapshot,
};

async fn press(firmware: &mut FirmwareHarness, button: Button) -> Snapshot {
    firmware
        .trigger(ButtonEvent::Pressed(button))
        .await
        .unwrap()
}

#[tokio::test]
async fn injected_buttons_drive_the_real_menu() {
    let mut firmware = FirmwareHarness::start().unwrap();
    assert_eq!(firmware.snapshot().processed_events, 0);

    let moved = firmware
        .trigger(ButtonEvent::Pressed(Button::Down))
        .await
        .unwrap();
    assert_eq!(moved.selected_index, 1);
    assert_eq!(moved.processed_events, 1);

    let released = firmware
        .trigger(ButtonEvent::Released(Button::Down))
        .await
        .unwrap();
    assert_eq!(released.selected_index, 1);
    assert_eq!(released.processed_events, 2);

    let previous = firmware
        .trigger(ButtonEvent::Pressed(Button::Up))
        .await
        .unwrap();
    assert_eq!(previous.selected_index, 0);
    let opened = firmware
        .trigger(ButtonEvent::Pressed(Button::Ok))
        .await
        .unwrap();
    assert_eq!(opened.menu_depth, 1);
    assert_eq!(opened.requested_action, None);

    let requested = firmware
        .trigger(ButtonEvent::Pressed(Button::Ok))
        .await
        .unwrap();
    assert_eq!(requested.menu_depth, 1);
    assert_eq!(requested.requested_action, Some(Request::SelectLocalGame));

    let closed = firmware
        .trigger(ButtonEvent::Pressed(Button::Left))
        .await
        .unwrap();
    assert_eq!(closed.menu_depth, 0);
    assert_eq!(closed.requested_action, None);
    firmware.shutdown().await.unwrap();
}

#[tokio::test]
async fn user_journey_visits_every_menu_and_dispatches_every_request() {
    let mut firmware = FirmwareHarness::start().unwrap();

    assert_eq!(press(&mut firmware, Button::Right).await.menu_depth, 1);
    assert_eq!(
        press(&mut firmware, Button::Ok).await.requested_action,
        Some(Request::SelectLocalGame)
    );
    let _ = press(&mut firmware, Button::Down).await;
    assert_eq!(
        press(&mut firmware, Button::Ok).await.requested_action,
        Some(Request::SelectOnlineGame)
    );
    assert_eq!(press(&mut firmware, Button::Left).await.menu_depth, 0);

    let _ = press(&mut firmware, Button::Down).await;
    let _ = press(&mut firmware, Button::Right).await;
    assert_eq!(
        press(&mut firmware, Button::Ok).await.requested_action,
        Some(Request::ShowConnectionStatus)
    );
    let _ = press(&mut firmware, Button::Down).await;
    assert_eq!(
        press(&mut firmware, Button::Ok).await.requested_action,
        Some(Request::ScanWifi)
    );
    let _ = press(&mut firmware, Button::Down).await;
    assert_eq!(
        press(&mut firmware, Button::Ok).await.requested_action,
        Some(Request::OpenNetworkSettings)
    );
    let _ = press(&mut firmware, Button::Left).await;

    let _ = press(&mut firmware, Button::Down).await;
    let _ = press(&mut firmware, Button::Right).await;
    assert_eq!(
        press(&mut firmware, Button::Ok).await.requested_action,
        Some(Request::StartPairing)
    );
    let _ = press(&mut firmware, Button::Down).await;
    assert_eq!(
        press(&mut firmware, Button::Ok).await.requested_action,
        Some(Request::ShowSessionStatus)
    );
    let _ = press(&mut firmware, Button::Left).await;

    let _ = press(&mut firmware, Button::Down).await;
    let _ = press(&mut firmware, Button::Right).await;
    assert_eq!(
        press(&mut firmware, Button::Ok).await.requested_action,
        Some(Request::CheckForUpdates)
    );
    let _ = press(&mut firmware, Button::Down).await;
    assert_eq!(
        press(&mut firmware, Button::Ok).await.requested_action,
        Some(Request::InstallUpdate)
    );
    let _ = press(&mut firmware, Button::Left).await;

    let _ = press(&mut firmware, Button::Down).await;
    assert_eq!(press(&mut firmware, Button::Right).await.menu_depth, 1);
    let empty = press(&mut firmware, Button::Ok).await;
    assert_eq!(empty.requested_action, None);
    assert_eq!(empty.selected_index, 0);
    let returned = press(&mut firmware, Button::Left).await;
    assert_eq!(returned.menu_depth, 0);
    assert_eq!(returned.selected_index, 4);

    firmware.shutdown().await.unwrap();
}

#[tokio::test]
async fn piece_events_are_observed_without_driving_the_menu() {
    let mut firmware = FirmwareHarness::start().unwrap();
    let piece = PieceEvent::Placed(BoardPosition::new(3, 4).unwrap());

    let snapshot = firmware.trigger(piece).await.unwrap();

    assert_eq!(snapshot.processed_events, 1);
    assert_eq!(snapshot.selected_index, 0);
    assert_eq!(snapshot.menu_depth, 0);
    assert_eq!(snapshot.requested_action, None);
    assert_eq!(snapshot.last_event, Some(HardwareEvent::Piece(piece)));
    firmware.shutdown().await.unwrap();
}

#[tokio::test]
async fn firmware_instances_are_isolated_and_restart_cleanly() {
    let mut first = FirmwareHarness::start().unwrap();
    let second = FirmwareHarness::start().unwrap();
    first
        .trigger(ButtonEvent::Pressed(Button::Down))
        .await
        .unwrap();
    assert_eq!(second.snapshot().processed_events, 0);
    first.shutdown().await.unwrap();
    second.shutdown().await.unwrap();
    let restarted = FirmwareHarness::start().unwrap();
    assert_eq!(restarted.snapshot().selected_index, 0);
    restarted.shutdown().await.unwrap();
}
