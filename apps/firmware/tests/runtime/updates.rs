//! "Check for Updates" through the production menu: a blocking item whose
//! result reaches the snapshot and releases the menu.

use std::{
    io::{Read, Write},
    net::TcpListener,
    sync::{
        Arc,
        atomic::{AtomicUsize, Ordering},
    },
    thread,
};

use firmware::{
    hardware::pins::{Button, ButtonEvent},
    harness::FirmwareHarness,
    menu::{
        Request,
        transitions::{Config, UpdateStatus},
    },
};

use crate::Navigator;

/// Serves one canned HTTP response on a local port, counting requests.
fn feed(response: String) -> (Navigator, Arc<AtomicUsize>) {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let url = format!("http://{}/releases/latest", listener.local_addr().unwrap());
    let requests = Arc::new(AtomicUsize::new(0));
    let served = requests.clone();
    thread::spawn(move || {
        for mut stream in listener.incoming().flatten() {
            let _ = stream.read(&mut [0; 4096]);
            served.fetch_add(1, Ordering::SeqCst);
            let _ = stream.write_all(response.as_bytes());
        }
    });
    let config = Config {
        update: Some(url),
        ..Config::offline()
    };
    let panel = Navigator::new(FirmwareHarness::with_config(&config).unwrap());
    (panel, requests)
}

#[tokio::test]
async fn a_newer_release_reaches_the_snapshot() {
    let body = r#"{"tag_name": "v99.0.0", "html_url": "https://example.invalid/v99.0.0"}"#;
    let (mut panel, _) = feed(format!(
        "HTTP/1.1 200 OK\r\nContent-Length: {}\r\nConnection: close\r\n\r\n{body}",
        body.len()
    ));

    panel.open(Request::CheckForUpdates).await;
    let snapshot = panel
        .firmware
        .until(|snapshot| snapshot.blocking.is_none())
        .await
        .unwrap();

    assert_eq!(
        snapshot.transitions.update,
        UpdateStatus::Available {
            version: semver::Version::new(99, 0, 0),
            page: "https://example.invalid/v99.0.0".into(),
        }
    );
    panel.firmware.shutdown().await.unwrap();
}

#[tokio::test]
async fn the_menu_holds_input_until_the_result_arrives() {
    // Accepts connections but never answers, so the check stays in flight.
    let silent = TcpListener::bind("127.0.0.1:0").unwrap();
    let config = Config {
        update: Some(format!(
            "http://{}/releases/latest",
            silent.local_addr().unwrap()
        )),
        ..Config::offline()
    };
    let mut panel = Navigator::new(FirmwareHarness::with_config(&config).unwrap());

    let checking = panel.open(Request::CheckForUpdates).await;
    assert_eq!(checking.blocking, Some(Request::CheckForUpdates));
    let blocked = panel
        .firmware
        .trigger(ButtonEvent::Pressed(Button::Up))
        .await
        .unwrap();
    assert_eq!(blocked.selected_index, checking.selected_index);
    assert_eq!(blocked.transitions.update, UpdateStatus::Checking);
    assert_eq!(blocked.requested_action, None);
    panel.firmware.shutdown().await.unwrap();
}

#[tokio::test]
async fn a_failed_check_releases_the_menu_and_can_be_retried() {
    let (mut panel, requests) = feed(
        "HTTP/1.1 503 Service Unavailable\r\nContent-Length: 0\r\nConnection: close\r\n\r\n".into(),
    );

    for attempt in 1..=2 {
        panel.open(Request::CheckForUpdates).await;
        let failed = panel
            .firmware
            .until(|snapshot| snapshot.blocking.is_none())
            .await
            .unwrap();
        assert!(
            matches!(&failed.transitions.update, UpdateStatus::Failed(cause) if cause.contains("503")),
            "{:?}",
            failed.transitions.update
        );
        assert_eq!(requests.load(Ordering::SeqCst), attempt);
    }
    // The menu navigates normally again.
    panel.open(Request::InstallUpdate).await;
    panel.firmware.shutdown().await.unwrap();
}

#[tokio::test]
async fn offline_firmware_reports_disabled_and_stays_navigable() {
    let mut panel = Navigator::start();
    panel.open(Request::CheckForUpdates).await;
    let snapshot = panel
        .firmware
        .until(|snapshot| snapshot.blocking.is_none())
        .await
        .unwrap();
    assert_eq!(snapshot.transitions.update, UpdateStatus::Disabled);
    panel.open(Request::InstallUpdate).await;
    panel.firmware.shutdown().await.unwrap();
}
