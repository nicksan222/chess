//! Product menu definition composed from the headless `menu` crate.

use ::menu::{Menu, MenuItem};

/// A user-visible screen controlled by the device coordinator.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Screen {
    /// Startup presentation before the coordinator declares the UI ready.
    Splash,
    /// Root list of user-selectable destinations.
    MainMenu,
    /// Network and internet connection information.
    ConnectionStatus,
    /// Local or online game configuration.
    GameSetup,
    /// Pairing progress and session confirmation.
    Pairing,
    /// Active-game status and controls.
    InGameHud,
    /// Software update status and controls.
    Update,
    /// User-adjustable device preferences.
    Settings,
    /// Completed-game result.
    Result,
    /// Recoverable error and retry controls.
    ErrorRecovery,
}

impl Screen {
    /// Returns whether the global status bar is visible on this screen.
    pub const fn shows_status_bar(self) -> bool {
        !matches!(self, Self::Splash)
    }
}

/// A request exposed by a selectable leaf in the product menu.
///
/// These values are placeholders for future external modules. The menu does not
/// execute them, and none are blocking until those integrations define their
/// completion and cancellation behavior.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Request {
    /// Select local game setup.
    SelectLocalGame,
    /// Select online game setup.
    SelectOnlineGame,
    /// Show current connection status.
    ShowConnectionStatus,
    /// Request a Wi-Fi scan.
    ScanWifi,
    /// Open externally managed network settings.
    OpenNetworkSettings,
    /// Start the externally managed pairing flow.
    StartPairing,
    /// Show current online-session status.
    ShowSessionStatus,
    /// Check whether a software update is available.
    CheckForUpdates,
    /// Start the externally managed update flow.
    InstallUpdate,
}

/// Game-mode choices.
pub static PLAY_MENU: Menu<'static, Request> = Menu::new(
    "Play",
    &[
        MenuItem::action("Local Game", Request::SelectLocalGame),
        MenuItem::action("Online Game", Request::SelectOnlineGame),
    ],
);

/// Connectivity information and controls.
pub static CONNECTION_MENU: Menu<'static, Request> = Menu::new(
    "Connection",
    &[
        MenuItem::action("Status", Request::ShowConnectionStatus),
        MenuItem::action("Scan Wi-Fi", Request::ScanWifi),
        MenuItem::action("Network Settings", Request::OpenNetworkSettings),
    ],
);

/// Pairing and online-session controls.
pub static PAIRING_MENU: Menu<'static, Request> = Menu::new(
    "Pairing",
    &[
        MenuItem::action("Start Pairing", Request::StartPairing),
        MenuItem::action("Session Status", Request::ShowSessionStatus),
    ],
);

/// Software update controls.
pub static UPDATE_MENU: Menu<'static, Request> = Menu::new(
    "Update",
    &[
        MenuItem::action("Check for Updates", Request::CheckForUpdates),
        MenuItem::action("Install Update", Request::InstallUpdate),
    ],
);

/// Settings placeholder; preference definitions will be supplied later.
pub static SETTINGS_MENU: Menu<'static, Request> = Menu::new("Settings", &[]);

/// Root menu presented after the splash screen.
pub static MAIN_MENU: Menu<'static, Request> = Menu::new(
    "Main Menu",
    &[
        MenuItem::submenu("Play", &PLAY_MENU),
        MenuItem::submenu("Connection", &CONNECTION_MENU),
        MenuItem::submenu("Pairing", &PAIRING_MENU),
        MenuItem::submenu("Update", &UPDATE_MENU),
        MenuItem::submenu("Settings", &SETTINGS_MENU),
    ],
);
