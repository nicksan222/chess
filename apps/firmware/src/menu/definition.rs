//! Product menu definition composed from the headless `menu` crate.
//!
//! Each module defines its own submenu as `MENU`; this file decides which ones
//! the product shows, and in what order. The menu performs no operation: every
//! leaf is a [`Request`] routed to the module that owns it.

use ::menu::{Menu, MenuItem};

use crate::modules::{Request, connection, pairing, play, update};

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

/// Settings placeholder; preference definitions will be supplied later.
pub static SETTINGS_MENU: Menu<'static, Request> = Menu::new("Settings", &[]);

/// Root menu presented after the splash screen.
pub static MAIN_MENU: Menu<'static, Request> = Menu::new(
    "Main Menu",
    &[
        MenuItem::submenu("Play", &play::MENU),
        MenuItem::submenu("Connection", &connection::MENU),
        MenuItem::submenu("Pairing", &pairing::MENU),
        MenuItem::submenu("Update", &update::MENU),
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
            ("Play", &play::MENU),
            ("Connection", &connection::MENU),
            ("Pairing", &pairing::MENU),
            ("Update", &update::MENU),
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
            &play::MENU,
            "Play",
            &[
                ("Local Game", Request::Play(play::Request::LocalGame)),
                ("Online Game", Request::Play(play::Request::OnlineGame)),
            ],
        );
        assert_menu(
            &connection::MENU,
            "Connection",
            &[
                ("Status", Request::Connection(connection::Request::Status)),
                (
                    "Scan Wi-Fi",
                    Request::Connection(connection::Request::ScanWifi),
                ),
                (
                    "Network Settings",
                    Request::Connection(connection::Request::NetworkSettings),
                ),
            ],
        );
        assert_menu(
            &pairing::MENU,
            "Pairing",
            &[
                ("Start Pairing", Request::Pairing(pairing::Request::Start)),
                (
                    "Session Status",
                    Request::Pairing(pairing::Request::SessionStatus),
                ),
            ],
        );
        assert_eq!(update::MENU.title(), "Update");
        let [check, install] = update::MENU.items() else {
            panic!("the update menu has two items");
        };
        assert_eq!(check.label(), "Check for Updates");
        assert_eq!(
            check.as_action(),
            Some(&Request::Update(update::Request::Check))
        );
        assert!(check.is_blocking());
        assert_eq!(
            check.escape_action(),
            Some(&Request::Update(update::Request::CancelCheck))
        );
        assert_eq!(install.label(), "Install Update");
        assert_eq!(
            install.as_action(),
            Some(&Request::Update(update::Request::Install))
        );
        assert!(!install.is_blocking());
        assert!(SETTINGS_MENU.is_empty());
    }

    #[test]
    fn every_submenu_is_navigable_without_requesting_external_work() {
        let submenus = [
            &play::MENU,
            &connection::MENU,
            &pairing::MENU,
            &update::MENU,
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
            Event::Activated(&Request::Play(play::Request::LocalGame))
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

    fn assert_menu(menu: &Menu<'static, Request>, title: &str, expected: &[(&str, Request)]) {
        assert_eq!(menu.title(), title);
        assert_eq!(menu.items().len(), expected.len());
        for (item, (label, request)) in menu.items().iter().zip(expected) {
            assert_eq!(item.label(), *label);
            assert_eq!(item.as_action(), Some(request));
            assert!(!item.is_blocking());
            assert_eq!(item.escape_action(), None);
        }
    }
}
