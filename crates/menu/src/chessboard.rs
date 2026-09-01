//! Menu tree for the physical chessboard.

use crate::{Menu, MenuCallbacks, MenuItem};

/// An action requested by the chessboard menu.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ChessboardAction {
    /// Start a game between two players using the physical board.
    StartLocalGame,
    /// Start the externally managed online-game flow.
    StartOnlineGame,
    /// Abort the active online-game flow.
    CancelOnlineGame,
    /// Present the current network connection information.
    ShowNetworkStatus,
    /// Start the externally managed network-setup flow.
    StartNetworkSetup,
    /// Forget the saved network and return to network setup.
    ForgetNetwork,
    /// Discard the current game and return the board to its initial state.
    ResetGame,
}

impl ChessboardAction {
    /// Invokes the one required callback corresponding to this action.
    pub fn dispatch<C>(self, callbacks: &mut C)
    where
        C: ChessboardCallbacks + ?Sized,
    {
        match self {
            Self::StartLocalGame => callbacks.start_local_game(),
            Self::StartOnlineGame => callbacks.start_online_game(),
            Self::CancelOnlineGame => callbacks.cancel_online_game(),
            Self::ShowNetworkStatus => callbacks.show_network_status(),
            Self::StartNetworkSetup => callbacks.start_network_setup(),
            Self::ForgetNetwork => callbacks.forget_network(),
            Self::ResetGame => callbacks.reset_game(),
        }
    }
}

/// Required external implementation of every chessboard menu action.
///
/// There are deliberately no default methods. Adding a menu action requires
/// every external integration to make an explicit handling decision.
pub trait ChessboardCallbacks {
    /// Starts a local two-player game.
    fn start_local_game(&mut self);

    /// Starts online-game discovery or connection.
    fn start_online_game(&mut self);

    /// Cancels online-game discovery or connection.
    fn cancel_online_game(&mut self);

    /// Presents current network information.
    fn show_network_status(&mut self);

    /// Starts network provisioning.
    fn start_network_setup(&mut self);

    /// Forgets saved network credentials.
    fn forget_network(&mut self);

    /// Resets the current game.
    fn reset_game(&mut self);
}

impl<T> MenuCallbacks<ChessboardAction> for T
where
    T: ChessboardCallbacks + ?Sized,
{
    fn on_action(&mut self, action: &ChessboardAction) {
        action.dispatch(self);
    }

    fn on_blocking_started(&mut self, action: &ChessboardAction) {
        action.dispatch(self);
    }

    fn on_blocking_aborted(
        &mut self,
        _operation: &ChessboardAction,
        escape_action: &ChessboardAction,
    ) {
        escape_action.dispatch(self);
    }
}

/// Choices available after selecting **Start Game**.
pub static START_GAME_MENU: Menu<'static, ChessboardAction> = Menu::new(
    "Start Game",
    &[
        MenuItem::action("1 vs 1", ChessboardAction::StartLocalGame),
        MenuItem::blocking_action(
            "1 vs Online",
            ChessboardAction::StartOnlineGame,
            ChessboardAction::CancelOnlineGame,
        ),
    ],
);

/// Confirmation required before forgetting the saved network.
pub static FORGET_NETWORK_MENU: Menu<'static, ChessboardAction> = Menu::new(
    "Forget Network?",
    &[MenuItem::action(
        "Confirm Forget",
        ChessboardAction::ForgetNetwork,
    )],
);

/// Network information and provisioning actions.
pub static NETWORK_MENU: Menu<'static, ChessboardAction> = Menu::new(
    "Network",
    &[
        MenuItem::action("Status", ChessboardAction::ShowNetworkStatus),
        MenuItem::action("Set Up Network", ChessboardAction::StartNetworkSetup),
        MenuItem::submenu("Forget Network", &FORGET_NETWORK_MENU),
    ],
);

/// Confirmation required before discarding the current game.
pub static RESET_GAME_MENU: Menu<'static, ChessboardAction> = Menu::new(
    "Reset Game?",
    &[MenuItem::action(
        "Confirm Reset",
        ChessboardAction::ResetGame,
    )],
);

/// Root menu presented by the chessboard.
pub static MAIN_MENU: Menu<'static, ChessboardAction> = Menu::new(
    "Main Menu",
    &[
        MenuItem::submenu("Start Game", &START_GAME_MENU),
        MenuItem::submenu("Network", &NETWORK_MENU),
        MenuItem::submenu("Reset Game", &RESET_GAME_MENU),
    ],
);
