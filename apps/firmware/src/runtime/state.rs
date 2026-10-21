use ::menu::{Input, MenuState};

use crate::{
    hardware::{
        HardwareEvent,
        pins::{Button, ButtonEvent},
    },
    menu::{
        MAIN_MENU, Request,
        transitions::{self, TransitionEvent, TransitionStatus, Transitions},
    },
};

/// A processed firmware state, suitable for displays and test assertions.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Snapshot {
    pub processed_events: u64,
    pub last_event: Option<HardwareEvent>,
    pub selected_index: usize,
    pub menu_depth: usize,
    /// Blocking menu operation holding input, if any.
    pub blocking: Option<Request>,
    /// Menu request awaiting an external implementation.
    pub requested_action: Option<Request>,
    /// Transition reports applied, counted separately from hardware events.
    pub reported_events: u64,
    /// What the integrations behind menu requests last reported.
    pub transitions: TransitionStatus,
}

pub(super) struct State {
    menu: MenuState<'static, Request>,
    transitions: Transitions,
    snapshot: Snapshot,
}

impl State {
    pub(super) fn new(transitions: Transitions) -> Self {
        Self {
            menu: MenuState::new(&MAIN_MENU),
            transitions,
            snapshot: Snapshot {
                processed_events: 0,
                last_event: None,
                selected_index: 0,
                menu_depth: 0,
                blocking: None,
                requested_action: None,
                reported_events: 0,
                transitions: TransitionStatus::default(),
            },
        }
    }

    pub(super) fn snapshot(&self) -> Snapshot {
        self.snapshot.clone()
    }

    pub(super) fn handle(&mut self, event: HardwareEvent) {
        self.snapshot.requested_action = None;
        if let HardwareEvent::Button(ButtonEvent::Pressed(button)) = event
            && let Some(input) = menu_input(button)
        {
            let request = match self.menu.handle(input) {
                ::menu::Event::Activated(action) | ::menu::Event::BlockingStarted(action) => {
                    Some(*action)
                }
                ::menu::Event::BlockingAborted { escape_action, .. } => Some(*escape_action),
                ::menu::Event::ExternalAction(action) => Some(action),
                _ => None,
            };
            if let Some(request) = request {
                self.transitions.handle(request);
                self.snapshot.requested_action = Some(request);
            }
        }
        let menu = self.menu.snapshot();
        self.snapshot.selected_index = menu.selected_index();
        self.snapshot.menu_depth = menu.depth();
        self.snapshot.blocking = self.menu.blocking_action().copied();
        self.snapshot.processed_events += 1;
        self.snapshot.last_event = Some(event);
    }

    /// Presents a result a transition reported, possibly from background work.
    pub(super) fn report(&mut self, event: TransitionEvent) {
        transitions::report(event, &mut self.menu, &mut self.snapshot.transitions);
        self.snapshot.blocking = self.menu.blocking_action().copied();
        self.snapshot.reported_events += 1;
    }
}

fn menu_input(button: Button) -> Option<Input> {
    match button {
        Button::Up => Some(Input::Up),
        Button::Down => Some(Input::Down),
        Button::Left => Some(Input::Left),
        Button::Right => Some(Input::Right),
        Button::Ok => Some(Input::Ok),
        Button::Reset
        | Button::Pass
        | Button::F1
        | Button::F2
        | Button::F3
        | Button::F4
        | Button::F5 => None,
    }
}
