use menu::{Event, Input, Menu, MenuCallbacks, MenuItem, MenuState};

use crate::common::{Action, Call, ROOT, Recorder};

static OPERATIONS: Menu<'static, Action> = Menu::new(
    "Operations",
    &[
        MenuItem::action("Wifi", Action::Wifi),
        MenuItem::blocking_action("Connect", Action::Start, Action::CancelStart),
    ],
);

fn calls_for(event: &Event<'_, Action>) -> Vec<Call<Action>> {
    let mut recorder = Recorder::default();
    event.dispatch(&mut recorder);
    recorder.calls
}

#[test]
fn navigation_only_events_invoke_no_callback() {
    let silent = [
        Event::SelectionChanged { selected: 3 },
        Event::Opened { depth: 1 },
        Event::Closed { depth: 0 },
        Event::InputBlocked,
        Event::Ignored,
        Event::DepthLimitReached,
    ];

    for event in silent {
        assert_eq!(calls_for(&event), [], "{event:?}");
    }
}

#[test]
fn each_action_bearing_event_invokes_exactly_its_callback() {
    assert_eq!(
        calls_for(&Event::Activated(&Action::Wifi)),
        [Call::Action(Action::Wifi)]
    );
    assert_eq!(
        calls_for(&Event::ExternalAction(Action::ShowHelp)),
        [Call::Action(Action::ShowHelp)]
    );
    assert_eq!(
        calls_for(&Event::BlockingStarted(&Action::Start)),
        [Call::BlockingStarted(Action::Start)]
    );
    assert_eq!(
        calls_for(&Event::BlockingAborted {
            operation: &Action::Start,
            escape_action: &Action::CancelStart,
        }),
        [Call::BlockingAborted {
            operation: Action::Start,
            escape_action: Action::CancelStart,
        }]
    );
}

#[test]
fn handle_and_dispatch_returns_the_event_it_dispatched() {
    let mut state = MenuState::new(&OPERATIONS);
    let mut recorder = Recorder::default();

    let events = [
        state.handle_and_dispatch(Input::Ok, &mut recorder),
        state.handle_and_dispatch(Input::Down, &mut recorder),
        state.handle_and_dispatch(Input::Ok, &mut recorder),
        state.handle_and_dispatch(Input::Up, &mut recorder),
        state.handle_and_dispatch(Input::Escape, &mut recorder),
    ];

    assert_eq!(
        events,
        [
            Event::Activated(&Action::Wifi),
            Event::SelectionChanged { selected: 1 },
            Event::BlockingStarted(&Action::Start),
            Event::InputBlocked,
            Event::BlockingAborted {
                operation: &Action::Start,
                escape_action: &Action::CancelStart,
            },
        ]
    );
    assert_eq!(
        recorder.calls,
        [
            Call::Action(Action::Wifi),
            Call::BlockingStarted(Action::Start),
            Call::BlockingAborted {
                operation: Action::Start,
                escape_action: Action::CancelStart,
            },
        ]
    );
}

#[test]
fn handle_and_dispatch_matches_handle() {
    let inputs = [
        Input::Ok,
        Input::Left,
        Input::Down,
        Input::Right,
        Input::Left,
        Input::Escape,
        Input::Escape,
    ];
    let mut plain = MenuState::new(&ROOT);
    let mut dispatched = MenuState::new(&ROOT);
    let mut recorder = Recorder::default();

    for input in inputs {
        assert_eq!(
            plain.handle(input),
            dispatched.handle_and_dispatch(input, &mut recorder),
            "{input:?}"
        );
    }
}

#[test]
fn callbacks_can_be_used_as_trait_objects() {
    let mut state = MenuState::new(&OPERATIONS);
    let mut recorder = Recorder::default();
    let callbacks: &mut dyn MenuCallbacks<Action> = &mut recorder;

    let _ = state.handle_and_dispatch(Input::Ok, callbacks);
    assert_eq!(recorder.calls, [Call::Action(Action::Wifi)]);
}
