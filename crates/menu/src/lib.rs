//! A `no_std`, integration-neutral menu model.
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
//! controls, and may contain further submenus up to [`MAX_MENU_DEPTH`].
//!
//! ```
//! use menu::{Event, Input, Menu, MenuItem, MenuState};
//!
//! #[derive(Debug, Eq, PartialEq)]
//! enum Action {
//!     ToggleVoice,
//! }
//!
//! let voice_items = [MenuItem::action("Enabled", Action::ToggleVoice)];
//! let voice = Menu::new("Voice", &voice_items);
//! let settings_items = [MenuItem::submenu("Voice", &voice)];
//! let settings = Menu::new("Settings", &settings_items);
//! let mut state = MenuState::new(&settings);
//!
//! assert_eq!(state.handle(Input::Ok), Event::Opened { depth: 1 });
//! assert_eq!(state.current_menu().title(), "Voice");
//! ```
//!
//! Display drivers, button polling, chess rules, and action execution remain
//! outside this crate.

#![no_std]
#![forbid(unsafe_code)]
#![warn(missing_docs)]

mod model;
mod navigation;

pub use model::{Command, Input, Menu, MenuControls, MenuDefinition, MenuItem};
pub use navigation::{Event, ExternalBehavior, MAX_MENU_DEPTH, MenuSnapshot, MenuState};
