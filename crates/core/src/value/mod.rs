//! Small semantic values shared by application-facing crates.

mod percentage;
mod toggle;

pub use percentage::{InvalidPercentage, Percentage};
pub use toggle::Toggle;
