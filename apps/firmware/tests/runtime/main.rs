//! Fast, Docker-free tests of the production runtime with injected hardware.

mod gpio;
mod navigator;

use navigator::Navigator;

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
async fn user_journey_dispatches_every_menu_request() {
    let mut panel = Navigator::start();

    for request in navigator::every_request() {
        let snapshot = panel.open(request).await;
        assert_eq!(snapshot.requested_action, Some(request));
    }

    panel.firmware.shutdown().await.unwrap();
}

#[tokio::test]
async fn empty_settings_menu_opens_and_closes_without_a_request() {
    let mut firmware = FirmwareHarness::start().unwrap();
    for _ in 0..4 {
        press(&mut firmware, Button::Down).await;
    }
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

const NAVIGATION: [Button; 5] = [
    Button::Up,
    Button::Down,
    Button::Left,
    Button::Right,
    Button::Ok,
];

async fn release(firmware: &mut FirmwareHarness, button: Button) -> Snapshot {
    firmware
        .trigger(ButtonEvent::Released(button))
        .await
        .unwrap()
}

#[tokio::test]
async fn a_new_firmware_waits_at_the_top_of_the_main_menu() {
    let firmware = FirmwareHarness::start().unwrap();

    let snapshot = firmware.snapshot();

    assert_eq!(snapshot.processed_events, 0);
    assert_eq!(snapshot.last_event, None);
    assert_eq!(snapshot.selected_index, 0);
    assert_eq!(snapshot.menu_depth, 0);
    assert_eq!(snapshot.requested_action, None);
    firmware.shutdown().await.unwrap();
}

#[tokio::test]
async fn buttons_without_a_menu_role_never_move_or_activate_the_menu() {
    let mut firmware = FirmwareHarness::start().unwrap();
    press(&mut firmware, Button::Down).await; // Not at the default position.
    let before = firmware.snapshot();
    let mut processed = before.processed_events;

    for button in [
        Button::Reset,
        Button::Pass,
        Button::F1,
        Button::F2,
        Button::F3,
        Button::F4,
        Button::F5,
    ] {
        for event in [ButtonEvent::Pressed(button), ButtonEvent::Released(button)] {
            let snapshot = firmware.trigger(event).await.unwrap();
            processed += 1;
            assert_eq!(snapshot.processed_events, processed, "{event:?}");
            assert_eq!(snapshot.last_event, Some(HardwareEvent::Button(event)));
            assert_eq!(snapshot.selected_index, before.selected_index, "{event:?}");
            assert_eq!(snapshot.menu_depth, before.menu_depth, "{event:?}");
            assert_eq!(snapshot.requested_action, None, "{event:?}");
        }
    }
    firmware.shutdown().await.unwrap();
}

#[tokio::test]
async fn releasing_a_button_never_navigates_or_activates() {
    let mut firmware = FirmwareHarness::start().unwrap();
    press(&mut firmware, Button::Down).await;
    press(&mut firmware, Button::Ok).await; // Opens Connection.
    let opened = firmware.snapshot();
    assert_eq!(opened.menu_depth, 1);

    for button in NAVIGATION {
        let snapshot = release(&mut firmware, button).await;
        assert_eq!(snapshot.selected_index, opened.selected_index, "{button:?}");
        assert_eq!(snapshot.menu_depth, opened.menu_depth, "{button:?}");
        assert_eq!(snapshot.requested_action, None, "{button:?}");
    }

    // One physical press of Ok on a leaf is one request, however long it is held.
    let requested = press(&mut firmware, Button::Ok).await;
    assert_eq!(
        requested.requested_action,
        Some(Request::ShowConnectionStatus)
    );
    let released = release(&mut firmware, Button::Ok).await;
    assert_eq!(released.requested_action, None);
    firmware.shutdown().await.unwrap();
}

#[tokio::test]
async fn a_request_is_reported_by_exactly_one_snapshot() {
    let mut panel = Navigator::start();
    let requested = panel.open(Request::ScanWifi).await;
    assert_eq!(requested.requested_action, Some(Request::ScanWifi));

    let next = panel
        .firmware
        .trigger(PieceEvent::Removed(BoardPosition::new(0, 0).unwrap()))
        .await
        .unwrap();

    assert_eq!(next.requested_action, None);
    assert_eq!(next.selected_index, requested.selected_index);
    assert_eq!(next.menu_depth, requested.menu_depth);
    panel.firmware.shutdown().await.unwrap();
}

#[tokio::test]
async fn navigation_stops_at_both_ends_and_at_the_root() {
    let mut firmware = FirmwareHarness::start().unwrap();

    let top = press(&mut firmware, Button::Up).await;
    assert_eq!((top.selected_index, top.menu_depth), (0, 0));
    let root = press(&mut firmware, Button::Left).await;
    assert_eq!((root.selected_index, root.menu_depth), (0, 0));

    for _ in 0..20 {
        press(&mut firmware, Button::Down).await;
    }
    let last = firmware.snapshot();
    assert_eq!(
        last.selected_index, 4,
        "Down does not wrap past the last item"
    );
    let again = press(&mut firmware, Button::Down).await;
    assert_eq!(again.selected_index, 4);
    firmware.shutdown().await.unwrap();
}

#[tokio::test]
async fn right_activates_like_ok() {
    let mut firmware = FirmwareHarness::start().unwrap();
    press(&mut firmware, Button::Right).await; // Opens Play.
    let requested = press(&mut firmware, Button::Right).await;

    assert_eq!(requested.menu_depth, 1);
    assert_eq!(requested.requested_action, Some(Request::SelectLocalGame));
    firmware.shutdown().await.unwrap();
}

#[tokio::test]
async fn every_board_position_is_observed_placed_and_removed_without_side_effects() {
    let mut firmware = FirmwareHarness::start().unwrap();
    let mut processed = 0;

    for row in 0..BoardPosition::SIZE {
        for column in 0..BoardPosition::SIZE {
            let position = BoardPosition::new(row, column).unwrap();
            for piece in [PieceEvent::Placed(position), PieceEvent::Removed(position)] {
                let snapshot = firmware.trigger(piece).await.unwrap();
                processed += 1;
                assert_eq!(snapshot.processed_events, processed);
                assert_eq!(snapshot.last_event, Some(HardwareEvent::Piece(piece)));
                assert_eq!((snapshot.selected_index, snapshot.menu_depth), (0, 0));
                assert_eq!(snapshot.requested_action, None);
            }
        }
    }
    firmware.shutdown().await.unwrap();
}
