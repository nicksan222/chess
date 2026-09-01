use menu::{
    ChessboardAction, Event, FORGET_NETWORK_MENU, Input, MAIN_MENU, MenuState, NETWORK_MENU,
    RESET_GAME_MENU, START_GAME_MENU,
};

#[test]
fn main_menu_opens_start_game_choices() {
    let mut state = MenuState::new(&MAIN_MENU);

    assert_eq!(MAIN_MENU.title(), "Main Menu");
    assert_eq!(MAIN_MENU.items().len(), 3);
    assert_eq!(MAIN_MENU.items()[0].label(), "Start Game");
    assert_eq!(MAIN_MENU.items()[1].label(), "Network");
    assert_eq!(MAIN_MENU.items()[2].label(), "Reset Game");
    assert_eq!(state.handle(Input::Ok), Event::Opened { depth: 1 });
    assert_eq!(state.current_menu(), &START_GAME_MENU);
}

#[test]
fn start_game_choices_request_local_or_online_play() {
    let mut state = MenuState::new(&START_GAME_MENU);

    assert_eq!(START_GAME_MENU.items()[0].label(), "1 vs 1");
    assert_eq!(
        state.handle(Input::Ok),
        Event::Activated(&ChessboardAction::StartLocalGame)
    );

    assert_eq!(
        state.handle(Input::Down),
        Event::SelectionChanged { selected: 1 }
    );
    assert_eq!(START_GAME_MENU.items()[1].label(), "1 vs Online");
    assert!(START_GAME_MENU.items()[1].is_blocking());
    assert_eq!(
        START_GAME_MENU.items()[1].escape_action(),
        Some(&ChessboardAction::CancelOnlineGame)
    );
    assert_eq!(
        state.handle(Input::Ok),
        Event::BlockingStarted(&ChessboardAction::StartOnlineGame)
    );
    assert!(state.is_blocked());
    assert_eq!(
        state.blocking_action(),
        Some(&ChessboardAction::StartOnlineGame)
    );
    assert_eq!(
        state.blocking_escape_action(),
        Some(&ChessboardAction::CancelOnlineGame)
    );
    let snapshot = state.snapshot();
    assert!(snapshot.is_blocked());
    assert_eq!(snapshot.blocking_action(), state.blocking_action());
    assert_eq!(
        snapshot.blocking_escape_action(),
        state.blocking_escape_action()
    );
    assert_eq!(state.handle(Input::Down), Event::InputBlocked);

    assert_eq!(
        state.handle(Input::Escape),
        Event::BlockingAborted {
            operation: &ChessboardAction::StartOnlineGame,
            escape_action: &ChessboardAction::CancelOnlineGame,
        }
    );
    assert!(!state.is_blocked());

    assert_eq!(
        state.handle(Input::Ok),
        Event::BlockingStarted(&ChessboardAction::StartOnlineGame)
    );
    assert_eq!(state.unblock(), Some(&ChessboardAction::StartOnlineGame));
    assert!(!state.is_blocked());
}

#[test]
fn network_menu_exposes_status_setup_and_confirmed_forget() {
    let mut state = MenuState::new(&NETWORK_MENU);

    assert_eq!(
        state.handle(Input::Ok),
        Event::Activated(&ChessboardAction::ShowNetworkStatus)
    );
    assert_eq!(
        state.handle(Input::Down),
        Event::SelectionChanged { selected: 1 }
    );
    assert_eq!(
        state.handle(Input::Ok),
        Event::Activated(&ChessboardAction::StartNetworkSetup)
    );
    assert_eq!(
        state.handle(Input::Down),
        Event::SelectionChanged { selected: 2 }
    );
    assert_eq!(state.handle(Input::Ok), Event::Opened { depth: 1 });
    assert_eq!(state.current_menu(), &FORGET_NETWORK_MENU);

    assert_eq!(state.handle(Input::Left), Event::Closed { depth: 0 });
    assert_eq!(state.selected_index(), 2);

    assert_eq!(state.handle(Input::Ok), Event::Opened { depth: 1 });
    assert_eq!(
        state.handle(Input::Ok),
        Event::Activated(&ChessboardAction::ForgetNetwork)
    );
}

#[test]
fn resetting_a_game_requires_confirmation() {
    let mut state = MenuState::new(&MAIN_MENU);
    let _ = state.handle(Input::Down);
    let _ = state.handle(Input::Down);

    assert_eq!(state.handle(Input::Ok), Event::Opened { depth: 1 });
    assert_eq!(state.current_menu(), &RESET_GAME_MENU);
    assert_eq!(state.handle(Input::Left), Event::Closed { depth: 0 });
    assert_eq!(state.selected_index(), 2);

    assert_eq!(state.handle(Input::Ok), Event::Opened { depth: 1 });
    assert_eq!(
        state.handle(Input::Ok),
        Event::Activated(&ChessboardAction::ResetGame)
    );
}
