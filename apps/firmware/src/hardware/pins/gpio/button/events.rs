use crate::events::{Bus, Subscription};

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

/// Events produced by a button adapter.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum ButtonEvent {
    Pressed(Button),
    Released(Button),
}

pub type ButtonEventBus = Bus<ButtonEvent>;
pub type ButtonEventSubscription = Subscription<ButtonEvent>;
