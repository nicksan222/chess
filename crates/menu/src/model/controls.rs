use super::{Command, Input};

/// Reusable bindings from semantic inputs to headless commands.
#[derive(Debug, Eq, PartialEq)]
pub struct MenuControls<A> {
    up: Command<A>,
    down: Command<A>,
    left: Command<A>,
    right: Command<A>,
    ok: Command<A>,
    escape: Command<A>,
}

impl<A> MenuControls<A> {
    /// Creates a complete set of explicit button bindings.
    pub const fn new(
        up: Command<A>,
        down: Command<A>,
        left: Command<A>,
        right: Command<A>,
        ok: Command<A>,
        escape: Command<A>,
    ) -> Self {
        Self {
            up,
            down,
            left,
            right,
            ok,
            escape,
        }
    }

    /// Creates conventional vertical-list controls.
    ///
    /// Up and down move the cursor, left and escape return to the parent, and
    /// both right and OK activate the selected item.
    pub const fn list() -> Self {
        Self::new(
            Command::SelectPrevious,
            Command::SelectNext,
            Command::GoBack,
            Command::Activate,
            Command::Activate,
            Command::GoBack,
        )
    }

    /// Returns the command bound to `input`.
    pub const fn command(&self, input: Input) -> &Command<A> {
        match input {
            Input::Up => &self.up,
            Input::Down => &self.down,
            Input::Left => &self.left,
            Input::Right => &self.right,
            Input::Ok => &self.ok,
            Input::Escape => &self.escape,
        }
    }
}

impl<A> Default for MenuControls<A> {
    fn default() -> Self {
        Self::list()
    }
}
