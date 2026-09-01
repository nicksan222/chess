//! Menu tree for the physical chessboard.

use crate::{Menu, MenuItem};

/// An action requested by the chessboard menu.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ChessboardAction {
    /// Start a game between two players using the physical board.
    StartLocalGame,
    /// Start the externally managed online-game flow.
    StartOnlineGame,
    /// Present the current network connection information.
    ShowNetworkStatus,
    /// Start the externally managed network-setup flow.
    StartNetworkSetup,
    /// Forget the saved network and return to network setup.
    ForgetNetwork,
    /// Discard the current game and return the board to its initial state.
    ResetGame,
}

/// Choices available after selecting **Start Game**.
pub static START_GAME_MENU: Menu<'static, ChessboardAction> = Menu::new(
    "Start Game",
    &[
        MenuItem::action("1 vs 1", ChessboardAction::StartLocalGame),
        MenuItem::action("1 vs Online", ChessboardAction::StartOnlineGame),
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
