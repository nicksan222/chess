use menu::{
    Command, Event, ExternalBehavior, Input, Menu, MenuCallbacks, MenuItem, MenuSnapshot, MenuState,
};

use crate::common::{Action, ROOT};

struct ReadOnlyGame {
    can_pass: bool,
}

#[derive(Default)]
struct HardwareBehavior {
    inputs_seen: usize,
}

#[derive(Default)]
struct CallbackCounts {
    actions: usize,
    blocking_starts: usize,
    blocking_aborts: usize,
}

impl MenuCallbacks<Action> for CallbackCounts {
    fn on_action(&mut self, _action: &Action) {
        self.actions += 1;
    }

    fn on_blocking_started(&mut self, _action: &Action) {
        self.blocking_starts += 1;
    }

    fn on_blocking_aborted(&mut self, _operation: &Action, _escape_action: &Action) {
        self.blocking_aborts += 1;
    }
}

impl ExternalBehavior<ReadOnlyGame, Action> for HardwareBehavior {
    fn on_input(
        &mut self,
        game: &ReadOnlyGame,
        menu: MenuSnapshot<'_, Action>,
        input: Input,
    ) -> Option<Command<Action>> {
        self.inputs_seen += 1;

        if input == Input::Ok && game.can_pass && menu.menu().title() == "Chess" {
            Some(Command::Action(Action::Start))
        } else {
            None
        }
    }
}

#[test]
fn external_behavior_borrows_game_and_dispatches_its_action() {
    let game = ReadOnlyGame { can_pass: true };
    let mut hardware = HardwareBehavior::default();
    let mut callbacks = CallbackCounts::default();
    let mut state = MenuState::new(&ROOT);

    assert_eq!(
        state.handle_with_and_dispatch(Input::Ok, &game, &mut hardware, &mut callbacks),
        Event::ExternalAction(Action::Start)
    );
    assert_eq!(hardware.inputs_seen, 1);
    assert_eq!(callbacks.actions, 1);
    assert_eq!(callbacks.blocking_starts, 0);
    assert_eq!(callbacks.blocking_aborts, 0);
}

#[test]
fn no_external_override_falls_back_to_menu_controls() {
    let game = ReadOnlyGame { can_pass: false };
    let mut hardware = HardwareBehavior::default();
    let mut state = MenuState::new(&ROOT);

    assert_eq!(
        state.handle_with(Input::Down, &game, &mut hardware),
        Event::SelectionChanged { selected: 1 }
    );
    assert_eq!(hardware.inputs_seen, 1);
}

#[test]
fn blocking_state_cannot_be_bypassed_by_external_behavior() {
    let game = ReadOnlyGame { can_pass: true };
    let mut hardware = HardwareBehavior::default();
    let items = [MenuItem::blocking_action(
        "Connect",
        Action::Start,
        Action::CancelStart,
    )];
    let menu = Menu::new("Online", &items);
    let mut state = MenuState::new(&menu);

    assert_eq!(
        state.handle(Input::Ok),
        Event::BlockingStarted(&Action::Start)
    );
    assert_eq!(
        state.handle_with(Input::Ok, &game, &mut hardware),
        Event::InputBlocked
    );
    assert_eq!(hardware.inputs_seen, 0);

    assert_eq!(
        state.handle_with(Input::Escape, &game, &mut hardware),
        Event::BlockingAborted {
            operation: &Action::Start,
            escape_action: &Action::CancelStart,
        }
    );
    assert_eq!(hardware.inputs_seen, 0);
}
