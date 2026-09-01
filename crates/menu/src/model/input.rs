/// A semantic input understood by the menu state.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Input {
    /// Up button.
    Up,
    /// Down button.
    Down,
    /// Left button.
    Left,
    /// Right button.
    Right,
    /// OK button.
    Ok,
    /// Cancel the current operation or return to the parent menu.
    Escape,
}
