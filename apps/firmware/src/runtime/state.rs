use menu::{ChessboardAction, Input, MAIN_MENU, MenuState};

use crate::events::{Button, Event};

/// A processed firmware state, suitable for displays and test assertions.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Snapshot {
    pub processed_events: u64,
    pub last_event: Option<Event>,
    pub selected_index: usize,
    pub menu_depth: usize,
    /// Requested operation; game/network execution is not implemented yet.
    pub requested_action: Option<ChessboardAction>,
}

pub(super) struct State {
    menu: MenuState<'static, ChessboardAction>,
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

    pub(super) fn handle(&mut self, event: Event) {
        self.snapshot.requested_action = None;
        if let Event::ButtonPressed(button) = event {
            if let Some(input) = menu_input(button) {
                self.snapshot.requested_action = match self.menu.handle(input) {
                    menu::Event::Activated(action) | menu::Event::BlockingStarted(action) => {
                        Some(*action)
                    }
                    menu::Event::BlockingAborted { escape_action, .. } => Some(*escape_action),
                    menu::Event::ExternalAction(action) => Some(action),
                    _ => None,
                };
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
        Button::Previous => Some(Input::Up),
        Button::Next => Some(Input::Down),
        Button::Back => Some(Input::Left),
        Button::Forward => Some(Input::Right),
        Button::Confirm => Some(Input::Ok),
        Button::Reset
        | Button::Pass
        | Button::FunctionOne
        | Button::FunctionTwo
        | Button::FunctionThree
        | Button::FunctionFour
        | Button::FunctionFive => None,
    }
}
