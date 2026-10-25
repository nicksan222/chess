#![allow(
    dead_code,
    reason = "each test crate uses a different subset of the shared helpers"
)]

use menu::{Command, Event, Input, Menu, MenuCallbacks, MenuControls, MenuItem, MenuState};

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) enum Action {
    Start,
    CancelStart,
    Wifi,
    DecreaseVolume,
    IncreaseVolume,
    ShowHelp,
}

pub(crate) static SETTINGS: Menu<'static, Action> = Menu::with_controls(
    "Settings",
    &[MenuItem::action("WiFi", Action::Wifi)],
    MenuControls::new(
        Command::SelectPrevious,
        Command::SelectNext,
        Command::Action(Action::DecreaseVolume),
        Command::Action(Action::IncreaseVolume),
        Command::Activate,
        Command::GoBack,
    ),
);

pub(crate) static ROOT: Menu<'static, Action> = Menu::with_controls(
    "Chess",
    &[
        MenuItem::action("Start", Action::Start),
        MenuItem::submenu("Settings", &SETTINGS),
    ],
    MenuControls::new(
        Command::SelectPrevious,
        Command::SelectNext,
        Command::Ignore,
        Command::Activate,
        Command::Action(Action::ShowHelp),
        Command::GoBack,
    ),
);

/// Every semantic input, for tests that must hold for all of them.
pub(crate) const ALL_INPUTS: [Input; 6] = [
    Input::Up,
    Input::Down,
    Input::Left,
    Input::Right,
    Input::Ok,
    Input::Escape,
];

/// One callback invocation, recorded with owned copies of its arguments.
#[derive(Debug, Eq, PartialEq)]
pub(crate) enum Call<A> {
    Action(A),
    BlockingStarted(A),
    BlockingAborted { operation: A, escape_action: A },
}

/// Callbacks that remember every invocation in order.
pub(crate) struct Recorder<A> {
    pub calls: Vec<Call<A>>,
}

impl<A> Default for Recorder<A> {
    fn default() -> Self {
        Self { calls: Vec::new() }
    }
}

impl<A: Clone> MenuCallbacks<A> for Recorder<A> {
    fn on_action(&mut self, action: &A) {
        self.calls.push(Call::Action(action.clone()));
    }

    fn on_blocking_started(&mut self, action: &A) {
        self.calls.push(Call::BlockingStarted(action.clone()));
    }

    fn on_blocking_aborted(&mut self, operation: &A, escape_action: &A) {
        self.calls.push(Call::BlockingAborted {
            operation: operation.clone(),
            escape_action: escape_action.clone(),
        });
    }
}

/// Applies `inputs` in order and returns every resulting event.
pub(crate) fn press_all<'a, A>(
    state: &mut MenuState<'a, A>,
    inputs: &[Input],
) -> Vec<Event<'a, A>> {
    inputs.iter().map(|&input| state.handle(input)).collect()
}

/// Returns whether `state` is displaying exactly `menu`, by identity rather than
/// structural equality.
pub(crate) fn is_showing<A>(state: &MenuState<'_, A>, menu: &Menu<'_, A>) -> bool {
    core::ptr::eq(state.current_menu(), menu)
}
