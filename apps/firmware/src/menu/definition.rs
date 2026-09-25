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

#[cfg(test)]
mod tests {
    use super::*;
    use ::menu::{Event, Input, MenuState};

    #[test]
    fn main_menu_composes_every_product_submenu() {
        let expected: [(&str, &Menu<'static, Request>); 5] = [
            ("Play", &PLAY_MENU),
            ("Connection", &CONNECTION_MENU),
            ("Pairing", &PAIRING_MENU),
            ("Update", &UPDATE_MENU),
            ("Settings", &SETTINGS_MENU),
        ];

        assert_eq!(MAIN_MENU.title(), "Main Menu");
        assert_eq!(MAIN_MENU.items().len(), expected.len());
        for (item, (label, submenu)) in MAIN_MENU.items().iter().zip(expected) {
            assert_eq!(item.label(), label);
            assert_eq!(item.as_submenu(), Some(submenu));
            assert_eq!(item.as_action(), None);
        }
    }

    #[test]
    fn submenus_expose_image_derived_placeholder_requests() {
        assert_menu(
            &PLAY_MENU,
            &[
                ("Local Game", Request::SelectLocalGame),
                ("Online Game", Request::SelectOnlineGame),
            ],
        );
        assert_menu(
            &CONNECTION_MENU,
            &[
                ("Status", Request::ShowConnectionStatus),
                ("Scan Wi-Fi", Request::ScanWifi),
                ("Network Settings", Request::OpenNetworkSettings),
            ],
        );
        assert_menu(
            &PAIRING_MENU,
            &[
                ("Start Pairing", Request::StartPairing),
                ("Session Status", Request::ShowSessionStatus),
            ],
        );
        assert_menu(
            &UPDATE_MENU,
            &[
                ("Check for Updates", Request::CheckForUpdates),
                ("Install Update", Request::InstallUpdate),
            ],
        );
        assert!(SETTINGS_MENU.is_empty());
    }

    #[test]
    fn every_submenu_is_navigable_without_requesting_external_work() {
        let submenus = [
            &PLAY_MENU,
            &CONNECTION_MENU,
            &PAIRING_MENU,
            &UPDATE_MENU,
            &SETTINGS_MENU,
        ];

        for (index, submenu) in submenus.into_iter().enumerate() {
            let mut state = MenuState::new(&MAIN_MENU);
            for selected in 0..index {
                assert_eq!(
                    state.handle(Input::Down),
                    Event::SelectionChanged {
                        selected: selected + 1
                    }
                );
            }
            assert_eq!(state.handle(Input::Right), Event::Opened { depth: 1 });
            assert_eq!(state.current_menu(), submenu);
            assert_eq!(state.handle(Input::Left), Event::Closed { depth: 0 });
            assert_eq!(state.selected_index(), index);
        }
    }

    #[test]
    fn placeholder_requests_are_immediate_and_non_blocking() {
        let mut state = MenuState::new(&MAIN_MENU);
        assert_eq!(state.handle(Input::Ok), Event::Opened { depth: 1 });
        assert_eq!(
            state.handle(Input::Ok),
            Event::Activated(&Request::SelectLocalGame)
        );
        assert!(!state.is_blocked());
    }

    #[test]
    fn status_bar_policy_covers_every_screen() {
        let visible = [
            Screen::MainMenu,
            Screen::ConnectionStatus,
            Screen::GameSetup,
            Screen::Pairing,
            Screen::InGameHud,
            Screen::Update,
            Screen::Settings,
            Screen::Result,
            Screen::ErrorRecovery,
        ];
        assert!(!Screen::Splash.shows_status_bar());
        assert!(visible.into_iter().all(Screen::shows_status_bar));
    }

    fn assert_menu(menu: &Menu<'static, Request>, expected: &[(&str, Request)]) {
        assert_eq!(menu.items().len(), expected.len());
        for (item, (label, request)) in menu.items().iter().zip(expected) {
            assert_eq!(item.label(), *label);
            assert_eq!(item.as_action(), Some(request));
            assert!(!item.is_blocking());
            assert_eq!(item.escape_action(), None);
        }
    }
}
