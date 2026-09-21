use firmware::menu::{
    CONNECTION_MENU, MAIN_MENU, PAIRING_MENU, PLAY_MENU, Request, SETTINGS_MENU, Screen,
    UPDATE_MENU,
};
use menu::{Event, Input, Menu, MenuState};

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
                    selected: selected + 1,
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
