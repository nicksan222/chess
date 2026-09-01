use menu::{ChessboardAction, ChessboardCallbacks, Event, Input, MAIN_MENU, MenuState};

#[derive(Default)]
struct FirmwareHarness {
    actions: Vec<ChessboardAction>,
}

impl ChessboardCallbacks for FirmwareHarness {
    fn start_local_game(&mut self) {
        self.actions.push(ChessboardAction::StartLocalGame);
    }

    fn start_online_game(&mut self) {
        self.actions.push(ChessboardAction::StartOnlineGame);
    }

    fn cancel_online_game(&mut self) {
        self.actions.push(ChessboardAction::CancelOnlineGame);
    }

    fn show_network_status(&mut self) {
        self.actions.push(ChessboardAction::ShowNetworkStatus);
    }

    fn start_network_setup(&mut self) {
        self.actions.push(ChessboardAction::StartNetworkSetup);
    }

    fn forget_network(&mut self) {
        self.actions.push(ChessboardAction::ForgetNetwork);
    }

    fn reset_game(&mut self) {
        self.actions.push(ChessboardAction::ResetGame);
    }
}

impl FirmwareHarness {
    fn press<'a>(
        &mut self,
        menu: &mut MenuState<'a, ChessboardAction>,
        input: Input,
    ) -> Event<'a, ChessboardAction> {
        menu.handle_and_dispatch(input, self)
    }
}

#[test]
fn player_starts_each_supported_game_mode() {
    let mut firmware = FirmwareHarness::default();
    let mut menu = MenuState::new(&MAIN_MENU);

    assert_eq!(
        firmware.press(&mut menu, Input::Ok),
        Event::Opened { depth: 1 }
    );
    assert_eq!(
        firmware.press(&mut menu, Input::Ok),
        Event::Activated(&ChessboardAction::StartLocalGame)
    );

    let mut menu = MenuState::new(&MAIN_MENU);
    let _ = firmware.press(&mut menu, Input::Ok);
    let _ = firmware.press(&mut menu, Input::Down);
    assert_eq!(
        firmware.press(&mut menu, Input::Ok),
        Event::BlockingStarted(&ChessboardAction::StartOnlineGame)
    );
    assert!(menu.is_blocked());
    assert_eq!(menu.unblock(), Some(&ChessboardAction::StartOnlineGame));

    assert_eq!(
        firmware.actions,
        [
            ChessboardAction::StartLocalGame,
            ChessboardAction::StartOnlineGame,
        ]
    );
}

#[test]
fn player_aborts_online_start_with_escape() {
    let mut firmware = FirmwareHarness::default();
    let mut menu = MenuState::new(&MAIN_MENU);

    let _ = firmware.press(&mut menu, Input::Ok);
    let _ = firmware.press(&mut menu, Input::Down);
    let _ = firmware.press(&mut menu, Input::Ok);

    assert_eq!(firmware.press(&mut menu, Input::Down), Event::InputBlocked);
    assert_eq!(
        firmware.press(&mut menu, Input::Escape),
        Event::BlockingAborted {
            operation: &ChessboardAction::StartOnlineGame,
            escape_action: &ChessboardAction::CancelOnlineGame,
        }
    );
    assert!(!menu.is_blocked());
    assert_eq!(
        firmware.actions,
        [
            ChessboardAction::StartOnlineGame,
            ChessboardAction::CancelOnlineGame,
        ]
    );
}

#[test]
fn player_uses_network_actions_and_can_cancel_forgetting_credentials() {
    let mut firmware = FirmwareHarness::default();
    let mut menu = MenuState::new(&MAIN_MENU);

    let _ = firmware.press(&mut menu, Input::Down);
    assert_eq!(
        firmware.press(&mut menu, Input::Ok),
        Event::Opened { depth: 1 }
    );
    let _ = firmware.press(&mut menu, Input::Ok);
    let _ = firmware.press(&mut menu, Input::Down);
    let _ = firmware.press(&mut menu, Input::Ok);
    let _ = firmware.press(&mut menu, Input::Down);

    assert_eq!(
        firmware.press(&mut menu, Input::Ok),
        Event::Opened { depth: 2 }
    );
    assert_eq!(
        firmware.press(&mut menu, Input::Left),
        Event::Closed { depth: 1 }
    );
    assert_eq!(
        firmware.actions,
        [
            ChessboardAction::ShowNetworkStatus,
            ChessboardAction::StartNetworkSetup,
        ]
    );

    let _ = firmware.press(&mut menu, Input::Ok);
    let _ = firmware.press(&mut menu, Input::Ok);
    assert_eq!(
        firmware.actions,
        [
            ChessboardAction::ShowNetworkStatus,
            ChessboardAction::StartNetworkSetup,
            ChessboardAction::ForgetNetwork,
        ]
    );
}

#[test]
fn player_can_cancel_then_confirm_game_reset() {
    let mut firmware = FirmwareHarness::default();
    let mut menu = MenuState::new(&MAIN_MENU);

    let _ = firmware.press(&mut menu, Input::Down);
    let _ = firmware.press(&mut menu, Input::Down);
    let _ = firmware.press(&mut menu, Input::Ok);
    assert_eq!(
        firmware.press(&mut menu, Input::Left),
        Event::Closed { depth: 0 }
    );
    assert!(firmware.actions.is_empty());

    let _ = firmware.press(&mut menu, Input::Ok);
    let _ = firmware.press(&mut menu, Input::Ok);
    assert_eq!(firmware.actions, [ChessboardAction::ResetGame]);
}
