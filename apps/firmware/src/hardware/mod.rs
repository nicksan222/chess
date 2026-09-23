//! Thin adapters over the board's physical interfaces.

pub mod display;
pub mod events;
pub mod pins;

pub use events::{
    BoardPosition, HardwareEvent, HardwareEventBus, HardwareEventSubscription, PieceEvent,
};
