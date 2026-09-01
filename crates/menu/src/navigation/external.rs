use crate::model::{Command, Input};

use super::snapshot::MenuSnapshot;

/// Optional external input policy with read-only application access.
///
/// `C` can be a chess game, settings model, or any other externally owned
/// value. Implementations may own mutable hardware adapters themselves, while
/// the context is always borrowed immutably. Returning `None` uses the current
/// menu's controls; returning `Some` overrides them for this input only.
pub trait ExternalBehavior<C: ?Sized, A> {
    /// Optionally supplies a command for one input.
    fn on_input(
        &mut self,
        context: &C,
        menu: MenuSnapshot<'_, A>,
        input: Input,
    ) -> Option<Command<A>>;
}
