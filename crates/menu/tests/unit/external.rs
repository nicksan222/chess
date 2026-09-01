use menu::{Command, Event, ExternalBehavior, Input, MenuSnapshot, MenuState};

use crate::common::{Action, ROOT};

struct ReadOnlyGame {
    can_pass: bool,
}

#[derive(Default)]
struct HardwareBehavior {
    inputs_seen: usize,
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
fn external_behavior_borrows_game_and_owns_adapter_state() {
    let game = ReadOnlyGame { can_pass: true };
    let mut hardware = HardwareBehavior::default();
    let mut state = MenuState::new(&ROOT);

    assert_eq!(
        state.handle_with(Input::Ok, &game, &mut hardware),
        Event::ExternalAction(Action::Start)
    );
    assert_eq!(hardware.inputs_seen, 1);
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
