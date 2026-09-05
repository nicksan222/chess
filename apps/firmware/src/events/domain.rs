/// A control-panel button expressed as a domain action.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Button {
    Previous,
    Next,
    Back,
    Forward,
    Confirm,
    Reset,
    Pass,
    FunctionOne,
    FunctionTwo,
    FunctionThree,
    FunctionFour,
    FunctionFive,
}

/// An event produced by the firmware's hardware adapters.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum Event {
    ButtonPressed(Button),
    ButtonReleased(Button),
}
