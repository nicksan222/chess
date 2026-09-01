/// A headless operation assigned to a menu button.
#[must_use = "a command must be applied or deliberately discarded"]
#[derive(Debug, Eq, PartialEq)]
pub enum Command<A> {
    /// Move the cursor toward the first entry.
    SelectPrevious,
    /// Move the cursor toward the last entry.
    SelectNext,
    /// Activate the selected item.
    Activate,
    /// Return to the parent menu.
    GoBack,
    /// Emit an application-defined action without changing menu state.
    Action(A),
    /// Deliberately do nothing.
    Ignore,
}
