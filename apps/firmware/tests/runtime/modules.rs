//! Modules through the real menu and runtime loop: the generic lifecycle of a
//! blocking request, driven by injected reports, and modules seen only through
//! their facades.

use chess::Square;

use std::net::TcpListener;

use firmware::{
    hardware::PieceEvent,
    harness::FirmwareHarness,
    modules::{
        Config, ModuleEvent, Phase, Request,
        connection::{self, Connection},
        firmware::{self as fw, Updates},
        pieces::Pieces,
        play,
    },
};

use crate::Navigator;

const CHECK: Request = Request::Updates(fw::Request::Check);

/// Holds the menu in "Check for Updates" with a feed that never answers, so
/// only injected reports move it on. The listener must outlive the test.
async fn blocked_on_check() -> (Navigator, TcpListener) {
    let silent = TcpListener::bind("127.0.0.1:0").unwrap();
    let config = Config {
        firmware: Some(format!("http://{}/", silent.local_addr().unwrap())),
        ..Config::offline()
    };
    let mut panel = Navigator::new(FirmwareHarness::with_config(&config).unwrap());
    let blocked = panel.open(CHECK).await;
    assert_eq!(blocked.blocking, Some(CHECK));
    // Let the real check's own progress report land, so injected reports are
    // the only ones acknowledged from here on.
    panel
        .firmware
        .until(|snapshot| snapshot.reported_events == 1)
        .await
        .unwrap();
    (panel, silent)
}

#[tokio::test]
async fn a_finished_report_releases_the_blocking_request() {
    let (mut panel, _feed) = blocked_on_check().await;

    let running = panel
        .firmware
        .report(ModuleEvent::new::<Updates>(
            Some(CHECK),
            Phase::Progress,
            fw::Status::Checking,
        ))
        .await
        .unwrap();
    assert_eq!(running.blocking, Some(CHECK));

    let unrelated = panel
        .firmware
        .report(ModuleEvent::new::<Updates>(
            None,
            Phase::Finished,
            fw::Status::Checking,
        ))
        .await
        .unwrap();
    assert_eq!(unrelated.blocking, Some(CHECK));

    let done = panel
        .firmware
        .report(ModuleEvent::new::<Updates>(
            Some(CHECK),
            Phase::Finished,
            fw::Status::UpToDate,
        ))
        .await
        .unwrap();
    assert_eq!(done.blocking, None);
    assert_eq!(done.modules.firmware, fw::Status::UpToDate);
    panel.open(Request::Updates(fw::Request::Install)).await;
    panel.firmware.shutdown().await.unwrap();
}

#[tokio::test]
async fn a_placeholder_finishes_at_once_and_leaves_the_menu_free() {
    let mut panel = Navigator::start();

    let opened = panel.open(Request::Play(play::Request::LocalGame)).await;
    assert_eq!(opened.blocking, None);
    let finished = panel
        .firmware
        .until(|snapshot| snapshot.reported_events == 1)
        .await
        .unwrap();
    assert_eq!(finished.blocking, None);
    panel
        .open(Request::Connection(connection::Request::ScanWifi))
        .await;
    panel.firmware.shutdown().await.unwrap();
}

#[tokio::test]
async fn a_module_without_menu_items_observes_piece_events() {
    let mut firmware = FirmwareHarness::start().unwrap();
    let square = Square::E4;
    assert_eq!(firmware.snapshot().modules.pieces.last(), None);

    let placed = firmware.trigger(PieceEvent::Placed(square)).await.unwrap();
    assert_eq!(
        placed.modules.pieces.last(),
        Some(PieceEvent::Placed(square))
    );
    assert!(placed.modules.pieces.is_occupied(square));
    assert_eq!(placed.modules.pieces.count(), 1);
    assert_eq!(placed.requested_action, None);
    assert_eq!(
        placed.reported_events, 0,
        "observed in the loop, not reported"
    );
    // Other modules see the same through the facade.
    assert_eq!(firmware.module::<Pieces>().status(), placed.modules.pieces);

    let removed = firmware.trigger(PieceEvent::Removed(square)).await.unwrap();
    assert!(!removed.modules.pieces.is_occupied(square));
    assert_eq!(removed.modules.pieces.count(), 0);
    assert_eq!(firmware.module::<Pieces>().status(), removed.modules.pieces);
    firmware.shutdown().await.unwrap();
}

#[tokio::test]
async fn offline_firmware_has_no_wifi_control_and_no_release_feed() {
    let firmware = FirmwareHarness::start().unwrap();

    assert!(matches!(
        firmware.module::<Connection>().status().await,
        Err(connection::Error::Unavailable)
    ));
    let update = firmware.module::<Updates>();
    assert!(!update.is_enabled());
    assert_eq!(update.check().await, fw::Status::Disabled);
    firmware.shutdown().await.unwrap();
}
