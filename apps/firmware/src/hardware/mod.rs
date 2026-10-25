//! Thin adapters over the board's physical interfaces.

pub mod button_panel;
mod buttons;
mod debounce;
pub mod display;
pub mod events;
pub mod hall;
#[cfg(target_os = "linux")]
pub mod linux_gpio;
#[cfg(target_os = "linux")]
pub mod linux_i2c;
pub mod pins;

pub(crate) use events::square;
pub use events::{
    BoardPosition, HardwareEvent, HardwareEventBus, HardwareEventSubscription, PieceEvent,
};
