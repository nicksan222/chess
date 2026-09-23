//! A `no_std`, headless menu state machine.
//!
//! The crate owns reusable menu primitives only: definitions, controls,
//! navigation state, blocking operations, and observable events. Applications
//! provide every label, action, control binding, submenu, and blocking policy.
//! Display drivers, product screens, hardware input, and action execution stay
//! outside this crate.
//!
//! # External definitions
//!
//! ```
//! use menu::{Event, Input, Menu, MenuItem, MenuState};
//!
//! #[derive(Debug, Eq, PartialEq)]
//! enum Action {
//!     OpenSettings,
//! }
//!
//! static ROOT: Menu<'static, Action> = Menu::new(
//!     "Main Menu",
//!     &[MenuItem::action("Settings", Action::OpenSettings)],
//! );
//!
//! let mut state = MenuState::new(&ROOT);
//! assert_eq!(
//!     state.handle(Input::Ok),
//!     Event::Activated(&Action::OpenSettings),
//! );
//! ```
//!
//! An application may instead provide a blocking entry. The menu then rejects
//! ordinary input until external code calls [`MenuState::unblock`], while escape
//! emits the externally supplied cancellation action.

#![no_std]
#![forbid(unsafe_code)]
#![warn(missing_docs)]

mod model;
mod navigation;

pub use model::{Command, Input, Menu, MenuControls, MenuDefinition, MenuItem};
pub use navigation::{
    Event, ExternalBehavior, MAX_MENU_DEPTH, MenuCallbacks, MenuSnapshot, MenuState,
};
