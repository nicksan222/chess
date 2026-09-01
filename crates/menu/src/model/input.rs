/// One of the five physical menu buttons.
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
}
