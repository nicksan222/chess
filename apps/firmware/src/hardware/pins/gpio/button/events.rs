/// The label printed beside a physical control-panel button.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Button {
    Up,
    Down,
    Left,
    Right,
    Ok,
    Reset,
    Pass,
    F1,
    F2,
    F3,
    F4,
    F5,
}

/// A debounced electrical transition produced by a physical button adapter.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ButtonEvent {
    Pressed(Button),
    Released(Button),
}
