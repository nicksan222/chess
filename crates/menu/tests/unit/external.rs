use menu::{
    Command, Event, ExternalBehavior, Input, Menu, MenuCallbacks, MenuItem, MenuSnapshot, MenuState,
};

use crate::common::{ALL_INPUTS, Action, Call, ROOT, Recorder, SETTINGS, is_showing};

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

/// Answers every input with the same command, recording what it was shown.
struct Always<F> {
    command: F,
    seen: Vec<(Input, usize, usize)>,
}

impl<F> Always<F> {
    fn new(command: F) -> Self {
        Self {
            command,
            seen: Vec::new(),
        }
    }
}

impl<C: ?Sized, F: Fn() -> Command<Action>> ExternalBehavior<C, Action> for Always<F> {
    fn on_input(
        &mut self,
        _context: &C,
        menu: MenuSnapshot<'_, Action>,
        input: Input,
    ) -> Option<Command<Action>> {
        self.seen.push((input, menu.depth(), menu.selected_index()));
        Some((self.command)())
    }
}

static OPERATIONS: Menu<'static, Action> = Menu::new(
    "Online",
    &[MenuItem::blocking_action(
        "Connect",
        Action::Start,
        Action::CancelStart,
    )],
);

#[test]
fn external_behavior_borrows_game_and_dispatches_its_action() {
    let game = ReadOnlyGame { can_pass: true };
    let mut hardware = HardwareBehavior::default();
    let mut callbacks = Recorder::default();
    let mut state = MenuState::new(&ROOT);

    assert_eq!(
        state.handle_with_and_dispatch(Input::Ok, &game, &mut hardware, &mut callbacks),
        Event::ExternalAction(Action::Start)
    );
    assert_eq!(hardware.inputs_seen, 1);
    assert_eq!(callbacks.calls, [Call::Action(Action::Start)]);
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
    assert_eq!(
        state.handle_with(Input::Ok, &game, &mut hardware),
        Event::Activated(&Action::ShowHelp)
    );
    assert_eq!(hardware.inputs_seen, 2);
}

#[test]
fn external_behavior_sees_the_state_before_its_input() {
    let mut always = Always::new(|| Command::SelectNext);
    let mut state = MenuState::new(&ROOT);

    let _ = state.handle_with(Input::Up, &(), &mut always);
    let _ = state.handle_with(Input::Escape, &(), &mut always);

    assert_eq!(always.seen, [(Input::Up, 0, 0), (Input::Escape, 0, 1)]);
}

#[test]
fn an_external_ignore_overrides_the_menu_controls() {
    let mut ignore = Always::new(|| Command::Ignore);
    let mut state = MenuState::new(&ROOT);

    for input in ALL_INPUTS {
        assert_eq!(state.handle_with(input, &(), &mut ignore), Event::Ignored);
    }
    assert_eq!(state.selected_index(), 0);
    assert!(state.is_at_root());
}

#[test]
fn external_navigation_commands_move_the_menu() {
    let mut state = MenuState::new(&ROOT);

    assert_eq!(
        state.handle_with(Input::Escape, &(), &mut Always::new(|| Command::SelectNext)),
        Event::SelectionChanged { selected: 1 }
    );
    assert_eq!(
        state.handle_with(Input::Up, &(), &mut Always::new(|| Command::Activate)),
        Event::Opened { depth: 1 }
    );
    assert!(is_showing(&state, &SETTINGS));
    assert_eq!(
        state.handle_with(Input::Down, &(), &mut Always::new(|| Command::GoBack)),
        Event::Closed { depth: 0 }
    );
    assert_eq!(
        state.handle_with(Input::Ok, &(), &mut Always::new(|| Command::SelectPrevious)),
        Event::SelectionChanged { selected: 0 }
    );
}

#[test]
fn external_actions_are_distinct_from_menu_actions() {
    let mut state = MenuState::new(&ROOT);
    let mut help = Always::new(|| Command::Action(Action::ShowHelp));

    assert_eq!(
        state.handle_with(Input::Ok, &(), &mut help),
        Event::ExternalAction(Action::ShowHelp)
    );
    assert_eq!(state.handle(Input::Ok), Event::Activated(&Action::ShowHelp));
}

#[test]
fn external_activate_can_start_a_blocking_operation() {
    let mut state = MenuState::new(&OPERATIONS);

    assert_eq!(
        state.handle_with(Input::Up, &(), &mut Always::new(|| Command::Activate)),
        Event::BlockingStarted(&Action::Start)
    );
    assert!(state.is_blocked());
}

#[test]
fn blocking_state_cannot_be_bypassed_by_external_behavior() {
    let game = ReadOnlyGame { can_pass: true };
    let mut hardware = HardwareBehavior::default();
    let mut state = MenuState::new(&OPERATIONS);

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

#[test]
fn context_and_behavior_may_be_unsized() {
    struct LabelBehavior;

    impl ExternalBehavior<str, Action> for LabelBehavior {
        fn on_input(
            &mut self,
            context: &str,
            _menu: MenuSnapshot<'_, Action>,
            _input: Input,
        ) -> Option<Command<Action>> {
            (context == "help").then_some(Command::Action(Action::ShowHelp))
        }
    }

    let mut state = MenuState::new(&ROOT);
    let behavior: &mut dyn ExternalBehavior<str, Action> = &mut LabelBehavior;
    let mut recorder = Recorder::default();
    let callbacks: &mut dyn MenuCallbacks<Action> = &mut recorder;

    assert_eq!(
        state.handle_with_and_dispatch(Input::Down, "help", behavior, callbacks),
        Event::ExternalAction(Action::ShowHelp)
    );
    assert_eq!(
        state.handle_with(Input::Down, "other", behavior),
        Event::SelectionChanged { selected: 1 }
    );
    assert_eq!(recorder.calls, [Call::Action(Action::ShowHelp)]);
}
