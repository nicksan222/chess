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
    modules::{
        Config, Request,
        update::{self, Error, Release, Status},
    },
};

use crate::Navigator;

const CHECK: Request = Request::Update(update::Request::Check);
const INSTALL: Request = Request::Update(update::Request::Install);

/// Serves one canned HTTP response on a local port, counting requests.
fn feed(response: String) -> (Navigator, Arc<AtomicUsize>) {
    let listener = TcpListener::bind("127.0.0.1:0").unwrap();
    let url = format!("http://{}/releases/latest", listener.local_addr().unwrap());
    let requests = Arc::new(AtomicUsize::new(0));
    let served = requests.clone();
    thread::spawn(move || {
        for mut stream in listener.incoming().flatten() {
            // Preflight probes connect without sending a request.
            if stream.read(&mut [0; 4096]).unwrap_or(0) > 0 {
                served.fetch_add(1, Ordering::SeqCst);
                let _ = stream.write_all(response.as_bytes());
            }
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

    panel.open(CHECK).await;
    let snapshot = panel
        .firmware
        .until(|snapshot| snapshot.blocking.is_none())
        .await
        .unwrap();

    assert_eq!(
        snapshot.modules.update,
        Status::Available(Release {
            version: semver::Version::new(99, 0, 0),
            page: "https://example.invalid/v99.0.0".into(),
        })
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

    let checking = panel.open(CHECK).await;
    assert_eq!(checking.blocking, Some(CHECK));
    let blocked = panel
        .firmware
        .trigger(ButtonEvent::Pressed(Button::Up))
        .await
        .unwrap();
    assert_eq!(blocked.selected_index, checking.selected_index);
    assert_eq!(blocked.modules.update, Status::Checking);
    assert_eq!(blocked.requested_action, None);
    panel.firmware.shutdown().await.unwrap();
}

#[tokio::test]
async fn a_failed_check_releases_the_menu_and_can_be_retried() {
    let (mut panel, requests) = feed(
        "HTTP/1.1 503 Service Unavailable\r\nContent-Length: 0\r\nConnection: close\r\n\r\n".into(),
    );

    for attempt in 1..=2 {
        panel.open(CHECK).await;
        let failed = panel
            .firmware
            .until(|snapshot| snapshot.blocking.is_none())
            .await
            .unwrap();
        assert_eq!(
            failed.modules.update,
            Status::Failed(Error::ServiceDown(503))
        );
        assert_eq!(requests.load(Ordering::SeqCst), attempt);
    }
    // The menu navigates normally again.
    panel.open(INSTALL).await;
    panel.firmware.shutdown().await.unwrap();
}

#[tokio::test]
async fn offline_firmware_reports_disabled_and_stays_navigable() {
    let mut panel = Navigator::start();
    panel.open(CHECK).await;
    let snapshot = panel
        .firmware
        .until(|snapshot| snapshot.blocking.is_none())
        .await
        .unwrap();
    assert_eq!(snapshot.modules.update, Status::Disabled);
    panel.open(INSTALL).await;
    panel.firmware.shutdown().await.unwrap();
}

#[tokio::test]
async fn without_internet_the_check_fails_offline_and_releases_the_menu() {
    // `.invalid` never resolves (RFC 6761), as when the device has no internet.
    let config = Config {
        update: Some("https://update-check.invalid/releases/latest".into()),
        ..Config::offline()
    };
    let mut panel = Navigator::new(FirmwareHarness::with_config(&config).unwrap());

    panel.open(CHECK).await;
    let snapshot = panel
        .firmware
        .until(|snapshot| snapshot.blocking.is_none())
        .await
        .unwrap();
    assert_eq!(
        snapshot.modules.update,
        Status::Failed(Error::Offline {
            host: "update-check.invalid".into()
        })
    );
    panel.open(INSTALL).await;
    panel.firmware.shutdown().await.unwrap();
}
