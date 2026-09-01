//! A `no_std` headless menu model and the chessboard's menu definition.
//!
//! Menus define labels, entries, and five-button behavior without knowing about
//! GPIO or pixels. [`MenuState`] applies input and exposes a read-only
//! [`MenuSnapshot`] for renderers.
//!
//! # External behavior
//!
//! [`ExternalBehavior`] may override individual inputs using immutable access to
//! application state. A chess game can therefore remain externally owned and
//! read-only while a separate behavior object owns hardware or adapter state.
//!
//! ```
//! use menu::{Event, Input, Menu, MenuItem, MenuState};
//!
//! #[derive(Debug, Eq, PartialEq)]
//! enum Action {
//!     StartGame,
//! }
//!
//! let items = [MenuItem::action("Start", Action::StartGame)];
//! let menu = Menu::new("Chess", &items);
//! let mut state = MenuState::new(&menu);
//!
//! assert_eq!(state.handle(Input::Ok), Event::Activated(&Action::StartGame));
//! ```
//!
//! Every entry may instead open another menu. Submenus use their own entries and
//! controls, and may contain further submenus up to [`MAX_MENU_DEPTH`]. The
//! chessboard's [`MAIN_MENU`] demonstrates this directly.
//!
//! ```
//! use menu::{Event, Input, MAIN_MENU, MenuState, START_GAME_MENU};
//!
//! let mut state = MenuState::new(&MAIN_MENU);
//!
//! assert_eq!(state.handle(Input::Ok), Event::Opened { depth: 1 });
//! assert_eq!(state.current_menu(), &START_GAME_MENU);
//! ```
//!
//! Display drivers, button polling, chess rules, and action execution remain
//! outside this crate.

#![no_std]
#![forbid(unsafe_code)]
#![warn(missing_docs)]

mod chessboard;
mod model;
mod navigation;

pub use chessboard::{
    ChessboardAction, FORGET_NETWORK_MENU, MAIN_MENU, NETWORK_MENU, RESET_GAME_MENU,
    START_GAME_MENU,
};
pub use model::{Command, Input, Menu, MenuControls, MenuDefinition, MenuItem};
pub use navigation::{Event, ExternalBehavior, MAX_MENU_DEPTH, MenuSnapshot, MenuState};
