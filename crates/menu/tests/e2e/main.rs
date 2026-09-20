use menu::{
    ChessboardAction, ChessboardCallbacks, Event, Input, Menu, MenuItem, MenuState, MAIN_MENU,
};

#[derive(Debug, Eq, PartialEq)]
enum Action {
    StartLocalGame,
    StartOnlineGame,
    ToggleSound,
    StartUpdate,
    CancelUpdate,
}

#[derive(Default)]
struct CallbackHarness {
    dispatched: Vec<ChessboardAction>,
}

impl ChessboardCallbacks for CallbackHarness {
    fn start_local_game(&mut self) {
        self.dispatched.push(ChessboardAction::StartLocalGame);
    }

    fn start_online_game(&mut self) {
        self.dispatched.push(ChessboardAction::StartOnlineGame);
    }

    fn cancel_online_game(&mut self) {
        self.dispatched.push(ChessboardAction::CancelOnlineGame);
    }

    fn show_network_status(&mut self) {
        self.dispatched.push(ChessboardAction::ShowNetworkStatus);
    }

    fn start_network_setup(&mut self) {
        self.dispatched.push(ChessboardAction::StartNetworkSetup);
    }

    fn forget_network(&mut self) {
        self.dispatched.push(ChessboardAction::ForgetNetwork);
    }

    fn reset_game(&mut self) {
        self.dispatched.push(ChessboardAction::ResetGame);
    }
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

#[test]
fn product_callback_dispatch_reaches_firmware_implementations() {
    let mut callbacks = CallbackHarness::default();
    let mut menu = MenuState::new(&MAIN_MENU);

    assert_eq!(
        menu.handle_and_dispatch(Input::Ok, &mut callbacks),
        Event::Opened { depth: 1 }
    );
    assert_eq!(
        menu.handle_and_dispatch(Input::Ok, &mut callbacks),
        Event::Activated(&ChessboardAction::StartLocalGame)
    );
    assert_eq!(
        menu.handle_and_dispatch(Input::Down, &mut callbacks),
        Event::SelectionChanged { selected: 1 }
    );
    assert_eq!(
        menu.handle_and_dispatch(Input::Ok, &mut callbacks),
        Event::BlockingStarted(&ChessboardAction::StartOnlineGame)
    );
    assert!(menu.is_blocked());
    assert_eq!(
        menu.handle_and_dispatch(Input::Escape, &mut callbacks),
        Event::BlockingAborted {
            operation: &ChessboardAction::StartOnlineGame,
            escape_action: &ChessboardAction::CancelOnlineGame,
        }
    );

    assert_eq!(
        callbacks.dispatched,
        [
            ChessboardAction::StartLocalGame,
            ChessboardAction::StartOnlineGame,
            ChessboardAction::CancelOnlineGame,
        ]
    );
}
