use super::{Command, Input};

/// Reusable bindings from the five physical buttons to headless commands.
#[derive(Debug, Eq, PartialEq)]
pub struct MenuControls<A> {
    up: Command<A>,
    down: Command<A>,
    left: Command<A>,
    right: Command<A>,
    ok: Command<A>,
}

impl<A> MenuControls<A> {
    /// Creates a complete set of explicit button bindings.
    pub const fn new(
        up: Command<A>,
        down: Command<A>,
        left: Command<A>,
        right: Command<A>,
        ok: Command<A>,
    ) -> Self {
        Self {
            up,
            down,
            left,
            right,
            ok,
        }
    }

    /// Creates conventional vertical-list controls.
    ///
    /// Up and down move the cursor, left returns to the parent, and both right
    /// and OK activate the selected item.
    pub const fn list() -> Self {
        Self::new(
            Command::SelectPrevious,
            Command::SelectNext,
            Command::GoBack,
            Command::Activate,
            Command::Activate,
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
        }
    }
}

impl<A> Default for MenuControls<A> {
    fn default() -> Self {
        Self::list()
    }
}
