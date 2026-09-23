use ::menu::{Input, MenuState};

use crate::{
    hardware::{
        HardwareEvent,
        pins::{Button, ButtonEvent},
    },
    menu::{MAIN_MENU, Request, transitions},
};

/// A processed firmware state, suitable for displays and test assertions.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Snapshot {
    pub processed_events: u64,
    pub last_event: Option<HardwareEvent>,
    pub selected_index: usize,
    pub menu_depth: usize,
    /// Menu request awaiting an external implementation.
    pub requested_action: Option<Request>,
}

pub(super) struct State {
    menu: MenuState<'static, Request>,
    snapshot: Snapshot,
}

impl State {
    pub(super) fn new() -> Self {
        Self {
            menu: MenuState::new(&MAIN_MENU),
            snapshot: Snapshot {
                processed_events: 0,
                last_event: None,
                selected_index: 0,
                menu_depth: 0,
                requested_action: None,
            },
        }
    }

    pub(super) fn snapshot(&self) -> Snapshot {
        self.snapshot.clone()
    }

    pub(super) fn handle(&mut self, event: HardwareEvent) {
        self.snapshot.requested_action = None;
        if let HardwareEvent::Button(ButtonEvent::Pressed(button)) = event {
            if let Some(input) = menu_input(button) {
                let request = match self.menu.handle(input) {
                    ::menu::Event::Activated(action) | ::menu::Event::BlockingStarted(action) => {
                        Some(*action)
                    }
                    ::menu::Event::BlockingAborted { escape_action, .. } => Some(*escape_action),
                    ::menu::Event::ExternalAction(action) => Some(action),
                    _ => None,
                };
                if let Some(request) = request {
                    transitions::handle(request);
                    self.snapshot.requested_action = Some(request);
                }
            }
        }
        let menu = self.menu.snapshot();
        self.snapshot.selected_index = menu.selected_index();
        self.snapshot.menu_depth = menu.depth();
        self.snapshot.processed_events += 1;
        self.snapshot.last_event = Some(event);
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
