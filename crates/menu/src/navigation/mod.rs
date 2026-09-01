//! Stateful traversal of declarative menu trees.

mod callbacks;
mod event;
mod external;
mod snapshot;
mod state;

pub use callbacks::MenuCallbacks;
pub use event::Event;
pub use external::ExternalBehavior;
pub use snapshot::MenuSnapshot;
pub use state::{MAX_MENU_DEPTH, MenuState};
