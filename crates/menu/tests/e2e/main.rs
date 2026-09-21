use menu::{Event, Input, Menu, MenuItem, MenuState};

#[derive(Debug, Eq, PartialEq)]
enum Action {
    StartLocalGame,
    StartOnlineGame,
    ToggleSound,
    StartUpdate,
    CancelUpdate,
}

static PLAY: Menu<'static, Action> = Menu::new(
    "Play",
    &[
        MenuItem::action("Local", Action::StartLocalGame),
        MenuItem::action("Online", Action::StartOnlineGame),
    ],
);
static SETTINGS: Menu<'static, Action> = Menu::new(
    "Settings",
    &[MenuItem::action("Sound", Action::ToggleSound)],
);
static ROOT: Menu<'static, Action> = Menu::new(
    "Main Menu",
    &[
        MenuItem::submenu("Play", &PLAY),
        MenuItem::submenu("Settings", &SETTINGS),
    ],
);
static OPERATIONS: Menu<'static, Action> = Menu::new(
    "Operations",
    &[MenuItem::blocking_action(
        "Update",
        Action::StartUpdate,
        Action::CancelUpdate,
    )],
);

#[test]
fn user_moves_through_submenus_and_returns_to_preserved_focus() {
    let mut menu = MenuState::new(&ROOT);

    assert_eq!(menu.handle(Input::Right), Event::Opened { depth: 1 });
    assert_eq!(menu.current_menu(), &PLAY);
    assert_eq!(
        menu.handle(Input::Ok),
        Event::Activated(&Action::StartLocalGame)
    );
    assert_eq!(
        menu.handle(Input::Down),
        Event::SelectionChanged { selected: 1 }
    );
    assert_eq!(
        menu.handle(Input::Ok),
        Event::Activated(&Action::StartOnlineGame)
    );
    assert_eq!(menu.handle(Input::Left), Event::Closed { depth: 0 });
    assert_eq!(menu.selected_index(), 0);

    assert_eq!(
        menu.handle(Input::Down),
        Event::SelectionChanged { selected: 1 }
    );
    assert_eq!(menu.handle(Input::Ok), Event::Opened { depth: 1 });
    assert_eq!(menu.current_menu(), &SETTINGS);
    assert_eq!(
        menu.handle(Input::Right),
        Event::Activated(&Action::ToggleSound)
    );
    assert_eq!(menu.handle(Input::Escape), Event::Closed { depth: 0 });
    assert_eq!(menu.selected_index(), 1);
}

#[test]
fn external_definition_controls_blocking_and_cancellation_journey() {
    let mut menu = MenuState::new(&OPERATIONS);

    assert_eq!(
        menu.handle(Input::Right),
        Event::BlockingStarted(&Action::StartUpdate)
    );
    assert_eq!(menu.handle(Input::Down), Event::InputBlocked);
    assert_eq!(menu.handle(Input::Ok), Event::InputBlocked);
    assert_eq!(
        menu.handle(Input::Escape),
        Event::BlockingAborted {
            operation: &Action::StartUpdate,
            escape_action: &Action::CancelUpdate,
        }
    );
    assert!(!menu.is_blocked());
}

#[test]
fn external_completion_restores_input_after_blocking_journey() {
    let mut menu = MenuState::new(&OPERATIONS);

    assert_eq!(
        menu.handle(Input::Ok),
        Event::BlockingStarted(&Action::StartUpdate)
    );
    assert_eq!(menu.unblock(), Some(&Action::StartUpdate));
    assert_eq!(
        menu.handle(Input::Ok),
        Event::BlockingStarted(&Action::StartUpdate)
    );
}
