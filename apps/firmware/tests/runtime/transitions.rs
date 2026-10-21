//! The generic lifecycle of a blocking transition, driven by injected reports
//! through the real menu and runtime loop.

use std::net::TcpListener;

use firmware::{
    harness::FirmwareHarness,
    menu::{
        Request,
        transitions::{Config, TransitionEvent, UpdateCheck, UpdateStatus},
    },
};

use crate::Navigator;

/// Holds the menu in "Check for Updates" with a feed that never answers, so
/// only injected reports move it on. The listener must outlive the test.
async fn blocked_on_check() -> (Navigator, TcpListener) {
    let silent = TcpListener::bind("127.0.0.1:0").unwrap();
    let config = Config {
        update: Some(format!("http://{}/", silent.local_addr().unwrap())),
    };
    let mut panel = Navigator::new(FirmwareHarness::with_config(&config).unwrap());
    let blocked = panel.open(Request::CheckForUpdates).await;
    assert_eq!(blocked.blocking, Some(Request::CheckForUpdates));
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
        .report(TransitionEvent::progress::<UpdateCheck>(
            UpdateStatus::Checking,
        ))
        .await
        .unwrap();
    assert_eq!(running.blocking, Some(Request::CheckForUpdates));

    let done = panel
        .firmware
        .report(TransitionEvent::finished::<UpdateCheck>(
            UpdateStatus::UpToDate,
        ))
        .await
        .unwrap();
    assert_eq!(done.blocking, None);
    assert_eq!(done.transitions.update, UpdateStatus::UpToDate);
    panel.open(Request::InstallUpdate).await;
    panel.firmware.shutdown().await.unwrap();
}
