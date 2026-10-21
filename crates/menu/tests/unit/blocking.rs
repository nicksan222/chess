use menu::{Command, Event, Input, Menu, MenuControls, MenuItem, MenuState};

use crate::common::{ALL_INPUTS, Action, is_showing};

static OPERATIONS: Menu<'static, Action> = Menu::new(
    "Operations",
    &[
        MenuItem::action("Help", Action::ShowHelp),
        MenuItem::blocking_action("Connect", Action::Start, Action::CancelStart),
    ],
);

static ROOT: Menu<'static, Action> = Menu::new(
    "Root",
    &[
        MenuItem::action("Wifi", Action::Wifi),
        MenuItem::submenu("Operations", &OPERATIONS),
    ],
);

/// Escape is bound to an action here, yet must still abort a blocking entry.
static ESCAPE_IS_AN_ACTION: Menu<'static, Action> = Menu::with_controls(
    "Custom",
    &[MenuItem::blocking_action(
        "Connect",
        Action::Start,
        Action::CancelStart,
    )],
    MenuControls::new(
        Command::SelectPrevious,
        Command::SelectNext,
        Command::GoBack,
        Command::Activate,
        Command::Activate,
        Command::Action(Action::ShowHelp),
    ),
);

fn blocked_in_operations() -> MenuState<'static, Action> {
    let mut state = MenuState::new(&ROOT);
    let _ = state.handle(Input::Down);
    let _ = state.handle(Input::Ok);
    let _ = state.handle(Input::Down);
    assert_eq!(
        state.handle(Input::Ok),
        Event::BlockingStarted(&Action::Start)
    );
    state
}

#[test]
fn activating_a_blocking_entry_starts_the_operation() {
    let state = blocked_in_operations();

    assert!(state.is_blocked());
    assert_eq!(state.blocking_action(), Some(&Action::Start));
    assert_eq!(state.blocking_escape_action(), Some(&Action::CancelStart));
}

#[test]
fn every_input_except_escape_is_blocked() {
    let mut state = blocked_in_operations();

    for input in ALL_INPUTS
        .into_iter()
        .filter(|&input| input != Input::Escape)
    {
        assert_eq!(state.handle(input), Event::InputBlocked, "{input:?}");
        assert!(state.is_blocked());
    }
}

#[test]
fn blocked_input_leaves_location_and_cursor_untouched() {
    let mut state = blocked_in_operations();

    for _ in 0..5 {
        let _ = state.handle(Input::Up);
        let _ = state.handle(Input::Left);
    }

    assert!(is_showing(&state, &OPERATIONS));
    assert_eq!(state.selected_index(), 1);
    assert_eq!(state.depth(), 1);
}

#[test]
fn escape_aborts_with_the_configured_cancellation_and_stays_in_place() {
    let mut state = blocked_in_operations();

    assert_eq!(
        state.handle(Input::Escape),
        Event::BlockingAborted {
            operation: &Action::Start,
            escape_action: &Action::CancelStart,
        }
    );
    assert!(!state.is_blocked());
    assert_eq!(state.blocking_action(), None);
    assert_eq!(state.blocking_escape_action(), None);
    assert!(is_showing(&state, &OPERATIONS));
    assert_eq!(state.selected_index(), 1);

    assert_eq!(state.handle(Input::Escape), Event::Closed { depth: 0 });
}

#[test]
fn escape_aborts_even_when_its_binding_is_an_action() {
    let mut state = MenuState::new(&ESCAPE_IS_AN_ACTION);

    assert_eq!(
        state.handle(Input::Escape),
        Event::Activated(&Action::ShowHelp)
    );
    assert_eq!(
        state.handle(Input::Ok),
        Event::BlockingStarted(&Action::Start)
    );
    assert_eq!(
        state.handle(Input::Escape),
        Event::BlockingAborted {
            operation: &Action::Start,
            escape_action: &Action::CancelStart,
        }
    );
}

#[test]
fn unblock_completes_the_operation_and_restores_input() {
    let mut state = blocked_in_operations();

    assert_eq!(state.unblock(), Some(&Action::Start));
    assert!(!state.is_blocked());
    assert_eq!(
        state.handle(Input::Up),
        Event::SelectionChanged { selected: 0 }
    );
}

#[test]
fn unblock_without_an_operation_reports_none() {
    let mut state = MenuState::new(&ROOT);

    assert_eq!(state.unblock(), None);

    let mut state = blocked_in_operations();
    let _ = state.unblock();
    assert_eq!(state.unblock(), None);
}

#[test]
fn escape_after_unblock_navigates_normally() {
    let mut state = blocked_in_operations();
    let _ = state.unblock();

    assert_eq!(state.handle(Input::Escape), Event::Closed { depth: 0 });
}

#[test]
fn unblock_after_abort_reports_none() {
    let mut state = blocked_in_operations();
    let _ = state.handle(Input::Escape);

    assert_eq!(state.unblock(), None);
}

#[test]
fn a_blocking_entry_can_be_started_again_after_finishing() {
    let mut state = blocked_in_operations();

    let _ = state.unblock();
    assert_eq!(
        state.handle(Input::Ok),
        Event::BlockingStarted(&Action::Start)
    );
    let _ = state.handle(Input::Escape);
    assert_eq!(
        state.handle(Input::Right),
        Event::BlockingStarted(&Action::Start)
    );
}
