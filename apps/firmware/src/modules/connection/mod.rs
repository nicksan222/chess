//! Typed, presentation-agnostic Wi-Fi control.
//!
//! Product types stay independent from NetworkManager, D-Bus, menus, and
//! displays; [`Connection`] translates them through an internal backend seam to
//! the maintained `nmrs` implementation, which tests replace with an in-memory
//! fake. NetworkManager is reached lazily, on the first operation, so building
//! the module never touches D-Bus; reaching it is bounded by
//! [`CONNECT_TIMEOUT`] and retried by the next operation after a failure. The
//! menu items are placeholders that finish immediately.

mod access_point;
mod backend;
mod client;
mod credentials;
mod error;
#[cfg(test)]
pub(super) mod fake;
mod hotspot;
mod link;
mod network_manager;
mod ssid;

use std::{future::Future, sync::Arc, time::Duration};

use ::menu::{Menu, MenuItem};
use tokio::{sync::OnceCell, time::timeout};

use super::{
    MissingDependency,
    module::{Context, Module, Reporter},
};
use client::Connectivity;

pub use access_point::{AccessPoint, Security};
pub use credentials::{Credentials, InvalidPassphrase, Passphrase};
pub use error::Error;
pub use hotspot::Hotspot;
pub use link::Link;
pub use ssid::{InvalidSsid, Ssid};

/// How this firmware instance controls Wi-Fi.
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub enum Settings {
    /// No Wi-Fi control: every operation fails with [`Error::Unavailable`].
    #[default]
    Unavailable,
    /// The system NetworkManager service and the board's radio.
    NetworkManager,
}

/// The placeholder menu items report nothing yet.
pub type Status = ();

/// Requests from the Connection menu.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Request {
    /// Show current connection status.
    Status,
    /// Request a Wi-Fi scan.
    ScanWifi,
    /// Open externally managed network settings.
    NetworkSettings,
}

/// Connectivity information and controls.
pub static MENU: Menu<'static, super::Request> = Menu::new(
    "Connection",
    &[
        MenuItem::action("Status", super::Request::Connection(Request::Status)),
        MenuItem::action("Scan Wi-Fi", super::Request::Connection(Request::ScanWifi)),
        MenuItem::action(
            "Network Settings",
            super::Request::Connection(Request::NetworkSettings),
        ),
    ],
);

/// How long reaching NetworkManager may take before an operation fails with
/// [`Error::TimedOut`].
pub const CONNECT_TIMEOUT: Duration = Duration::from_secs(5);

/// Product Wi-Fi operations. Clones share one connection to the Wi-Fi stack.
/// Other modules get it from the registry, never by building their own.
#[derive(Clone)]
pub struct Connection {
    wifi: Arc<Wifi>,
}

// One per firmware instance, shared behind an `Arc`, so size does not matter.
#[allow(clippy::large_enum_variant)]
enum Wifi {
    Unavailable,
    /// Connected on first use; a failed connection is retried on the next.
    NetworkManager(OnceCell<Connectivity>),
    #[cfg(test)]
    Fake(Connectivity<fake::FakeWifi>),
}

/// Runs `$call` on the configured backend's `Connectivity`, bound to `$wifi`.
macro_rules! with_wifi {
    ($self:ident, $wifi:ident => $call:expr) => {
        match &*$self.wifi {
            Wifi::Unavailable => Err(Error::Unavailable),
            Wifi::NetworkManager(cell) => {
                let $wifi = connected(cell, Connectivity::network_manager).await?;
                $call.await
            }
            #[cfg(test)]
            Wifi::Fake($wifi) => $call.await,
        }
    };
}

/// The value in `cell`, initialising it with `init` within
/// [`CONNECT_TIMEOUT`]. A failed or abandoned initialisation leaves the cell
/// empty, so the next caller tries again.
async fn connected<T, F, I>(cell: &OnceCell<T>, init: I) -> Result<&T, Error>
where
    I: FnOnce() -> F,
    F: Future<Output = Result<T, Error>>,
{
    timeout(CONNECT_TIMEOUT, cell.get_or_try_init(init))
        .await
        .map_err(|_| Error::TimedOut)?
}

impl Connection {
    fn new(settings: Settings) -> Self {
        let wifi = match settings {
            Settings::Unavailable => Wifi::Unavailable,
            Settings::NetworkManager => Wifi::NetworkManager(OnceCell::new()),
        };
        Self {
            wifi: Arc::new(wifi),
        }
    }

    /// A connection to an in-memory Wi-Fi stack.
    #[cfg(test)]
    pub(super) fn fake(wifi: fake::FakeWifi) -> Self {
        Self {
            wifi: Arc::new(Wifi::Fake(Connectivity::with_backend(wifi))),
        }
    }

    /// Reports the current client connection.
    pub async fn status(&self) -> Result<Link, Error> {
        with_wifi!(self, wifi => wifi.status())
    }

    /// Refreshes and returns visible networks, strongest first.
    pub async fn scan(&self) -> Result<Vec<AccessPoint>, Error> {
        with_wifi!(self, wifi => wifi.scan())
    }

    /// Starts the provisioning hotspot.
    pub async fn start_hotspot(&self, hotspot: &Hotspot) -> Result<(), Error> {
        with_wifi!(self, wifi => wifi.start_hotspot(hotspot))
    }

    /// Stops and removes the provisioning hotspot.
    pub async fn stop_hotspot(&self) -> Result<(), Error> {
        with_wifi!(self, wifi => wifi.stop_hotspot())
    }

    /// Stops hotspot mode and joins the selected client network.
    pub async fn connect(&self, ssid: &Ssid, credentials: &Credentials) -> Result<(), Error> {
        with_wifi!(self, wifi => wifi.connect(ssid, credentials))
    }
}

/// The connection module's engine.
pub(super) struct Engine {
    connection: Connection,
}

impl Module for Engine {
    type Settings = Settings;
    type Status = Status;
    type Request = Request;
    type Facade = Connection;

    const MENU: Option<&'static Menu<'static, crate::modules::Request>> = Some(&MENU);

    fn device() -> Settings {
        Settings::NetworkManager
    }

    fn new(settings: &Settings, _: &Context<'_, Status>) -> Result<Self, MissingDependency> {
        Ok(Self {
            connection: Connection::new(*settings),
        })
    }

    fn facade(&self) -> Connection {
        self.connection.clone()
    }

    fn request(&mut self, request: Request, report: Reporter<Status>) {
        // Placeholders until the connection screens exist.
        match request {
            Request::Status => report.done(),
            Request::ScanWifi => report.done(),
            Request::NetworkSettings => report.done(),
        }
    }
}

#[cfg(test)]
mod tests {
    use super::{fake::FakeWifi, *};

    #[test]
    fn the_product_uses_network_manager_and_tests_have_no_wifi() {
        assert_eq!(Engine::device(), Settings::NetworkManager);
        assert_eq!(Settings::default(), Settings::Unavailable);
    }

    #[tokio::test]
    async fn without_wifi_control_every_operation_is_unavailable() {
        let connection = Connection::new(Settings::Unavailable);
        assert!(matches!(connection.status().await, Err(Error::Unavailable)));
        assert!(matches!(connection.scan().await, Err(Error::Unavailable)));
        assert!(matches!(
            connection.stop_hotspot().await,
            Err(Error::Unavailable)
        ));
    }

    #[tokio::test]
    async fn the_facade_reaches_the_wifi_stack() {
        let connection = Connection::fake(FakeWifi::default().with_active_client("Home"));
        assert_eq!(
            connection.status().await.unwrap(),
            Link::Connected(Ssid::new("Home").unwrap())
        );
        assert!(connection.scan().await.unwrap().is_empty());
    }

    #[tokio::test(start_paused = true)]
    async fn a_stalled_network_manager_times_out_and_is_retried() {
        let cell = OnceCell::new();
        let stalled = connected(&cell, std::future::pending::<Result<u8, Error>>).await;
        assert!(matches!(stalled, Err(Error::TimedOut)), "{stalled:?}");
        assert!(!cell.initialized());

        let failed = connected(&cell, || async { Err(Error::UnknownState) }).await;
        assert!(matches!(failed, Err(Error::UnknownState)), "{failed:?}");
        assert!(!cell.initialized());

        assert_eq!(*connected(&cell, || async { Ok(7) }).await.unwrap(), 7);
        assert_eq!(*connected(&cell, || async { Ok(8) }).await.unwrap(), 7);
    }

    #[test]
    fn building_never_contacts_network_manager() {
        let connection = Connection::new(Settings::NetworkManager);
        let Wifi::NetworkManager(cell) = &*connection.wifi else {
            panic!("not NetworkManager");
        };
        assert!(!cell.initialized());
    }
}
