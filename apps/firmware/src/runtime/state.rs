use ::menu::MenuState;

use crate::{
    hardware::{HardwareEvent, pins::ButtonEvent},
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

impl Snapshot {
    fn initial() -> Self {
        Self {
            processed_events: 0,
            last_event: None,
            selected_index: 0,
            menu_depth: 0,
            blocking: None,
            requested_action: None,
            reported_events: 0,
            transitions: TransitionStatus::default(),
        }
    }
}

/// The menu and its integrations. The published [`Snapshot`] lives in the
/// caller's watch channel and is updated in place, so nothing is cloned per event.
pub(super) struct State {
    menu: MenuState<'static, Request>,
    transitions: Transitions,
}

impl State {
    pub(super) fn new(transitions: Transitions) -> Self {
        Self {
            menu: MenuState::new(&MAIN_MENU),
            transitions,
        }
    }

    pub(super) fn initial_snapshot(&self) -> Snapshot {
        Snapshot::initial()
    }

    pub(super) fn handle(&mut self, event: HardwareEvent, snapshot: &mut Snapshot) {
        snapshot.requested_action = None;
        if let Some(request) = self.request_for(event) {
            self.transitions.handle(request);
            snapshot.requested_action = Some(request);
        }
        self.refresh_snapshot(snapshot);
        snapshot.processed_events += 1;
        snapshot.last_event = Some(event);
    }

    /// Presents a result a transition reported, possibly from background work.
    pub(super) fn report(&mut self, event: TransitionEvent, snapshot: &mut Snapshot) {
        transitions::report(event, &mut self.menu, &mut snapshot.transitions);
        snapshot.blocking = self.menu.blocking_action().copied();
        snapshot.reported_events += 1;
    }

    /// Feeds a button press to the menu and returns the request it raised, if any.
    fn request_for(&mut self, event: HardwareEvent) -> Option<Request> {
        let HardwareEvent::Button(ButtonEvent::Pressed(button)) = event else {
            return None;
        };
        let input = button.menu_input()?;
        match self.menu.handle(input) {
            ::menu::Event::Activated(action) | ::menu::Event::BlockingStarted(action) => {
                Some(*action)
            }
            ::menu::Event::BlockingAborted { escape_action, .. } => Some(*escape_action),
            ::menu::Event::ExternalAction(action) => Some(action),
            _ => None,
        }
    }

    fn refresh_snapshot(&self, snapshot: &mut Snapshot) {
        let menu = self.menu.snapshot();
        snapshot.selected_index = menu.selected_index();
        snapshot.menu_depth = menu.depth();
        snapshot.blocking = self.menu.blocking_action().copied();
    }
}
