//! Whole user journeys through a small product-shaped menu, as firmware would
//! drive it: physical presses in, events and callbacks out.

#[path = "../common/mod.rs"]
mod common;

use common::{Call, Recorder};
use menu::{Command, Event, ExternalBehavior, Input, Menu, MenuItem, MenuSnapshot, MenuState};

#[derive(Clone, Debug, Eq, PartialEq)]
enum Action {
    StartLocalGame,
    StartOnlineGame,
    ToggleSound,
    StartUpdate,
    CancelUpdate,
    ResignGame,
}

static PLAY: Menu<'static, Action> = Menu::new(
    "Play",
    &[
        MenuItem::action("Local", Action::StartLocalGame),
        MenuItem::action("Online", Action::StartOnlineGame),
    ],
);
static SETTINGS: Menu<'static, Action> = Menu::new(
    "Settings",
    &[MenuItem::action("Sound", Action::ToggleSound)],
);
static ROOT: Menu<'static, Action> = Menu::new(
    "Main Menu",
    &[
        MenuItem::submenu("Play", &PLAY),
        MenuItem::submenu("Settings", &SETTINGS),
    ],
);
static PLAY_WITH_UPDATE: Menu<'static, Action> = Menu::new(
    "Main Menu",
    &[
        MenuItem::submenu("Play", &PLAY),
        MenuItem::submenu("Operations", &OPERATIONS),
    ],
);
static OPERATIONS: Menu<'static, Action> = Menu::new(
    "Operations",
    &[MenuItem::blocking_action(
        "Update",
        Action::StartUpdate,
        Action::CancelUpdate,
    )],
);

#[test]
fn user_moves_through_submenus_and_returns_to_preserved_focus() {
    let mut menu = MenuState::new(&ROOT);

    assert_eq!(menu.handle(Input::Right), Event::Opened { depth: 1 });
    assert_eq!(menu.current_menu(), &PLAY);
    assert_eq!(
        menu.handle(Input::Ok),
        Event::Activated(&Action::StartLocalGame)
    );
    assert_eq!(
        menu.handle(Input::Down),
        Event::SelectionChanged { selected: 1 }
    );
    assert_eq!(
        menu.handle(Input::Ok),
        Event::Activated(&Action::StartOnlineGame)
    );
    assert_eq!(menu.handle(Input::Left), Event::Closed { depth: 0 });
    assert_eq!(menu.selected_index(), 0);

    assert_eq!(
        menu.handle(Input::Down),
        Event::SelectionChanged { selected: 1 }
    );
    assert_eq!(menu.handle(Input::Ok), Event::Opened { depth: 1 });
    assert_eq!(menu.current_menu(), &SETTINGS);
    assert_eq!(
        menu.handle(Input::Right),
        Event::Activated(&Action::ToggleSound)
    );
    assert_eq!(menu.handle(Input::Escape), Event::Closed { depth: 0 });
    assert_eq!(menu.selected_index(), 1);
}

#[test]
fn external_definition_controls_blocking_and_cancellation_journey() {
    let mut menu = MenuState::new(&OPERATIONS);

    assert_eq!(
        menu.handle(Input::Right),
        Event::BlockingStarted(&Action::StartUpdate)
    );
    assert_eq!(menu.handle(Input::Down), Event::InputBlocked);
    assert_eq!(menu.handle(Input::Ok), Event::InputBlocked);
    assert_eq!(
        menu.handle(Input::Escape),
        Event::BlockingAborted {
            operation: &Action::StartUpdate,
            escape_action: &Action::CancelUpdate,
        }
    );
    assert!(!menu.is_blocked());
}

#[test]
fn external_completion_restores_input_after_blocking_journey() {
    let mut menu = MenuState::new(&OPERATIONS);

    assert_eq!(
        menu.handle(Input::Ok),
        Event::BlockingStarted(&Action::StartUpdate)
    );
    assert_eq!(menu.unblock(), Some(&Action::StartUpdate));
    assert_eq!(
        menu.handle(Input::Ok),
        Event::BlockingStarted(&Action::StartUpdate)
    );
}

#[test]
fn firmware_loop_runs_a_blocking_update_through_callbacks() {
    let mut menu = MenuState::new(&PLAY_WITH_UPDATE);
    let mut firmware = Recorder::default();
    let presses = [Input::Down, Input::Ok, Input::Ok, Input::Up, Input::Left];

    for input in presses {
        let _ = menu.handle_and_dispatch(input, &mut firmware);
    }
    assert!(menu.is_blocked());
    assert_eq!(firmware.calls, [Call::BlockingStarted(Action::StartUpdate)]);

    // The update finishes in the background; the user carries on.
    assert_eq!(menu.unblock(), Some(&Action::StartUpdate));
    assert_eq!(
        menu.handle_and_dispatch(Input::Left, &mut firmware),
        Event::Closed { depth: 0 }
    );
    assert_eq!(menu.selected_index(), 1);
    assert_eq!(firmware.calls.len(), 1);
}

#[test]
fn user_cancels_an_update_and_then_leaves_with_a_second_escape() {
    let mut menu = MenuState::new(&PLAY_WITH_UPDATE);
    let mut firmware = Recorder::default();

    for input in [
        Input::Down,
        Input::Ok,
        Input::Ok,
        Input::Escape,
        Input::Escape,
    ] {
        let _ = menu.handle_and_dispatch(input, &mut firmware);
    }

    assert_eq!(
        firmware.calls,
        [
            Call::BlockingStarted(Action::StartUpdate),
            Call::BlockingAborted {
                operation: Action::StartUpdate,
                escape_action: Action::CancelUpdate,
            },
        ]
    );
    assert!(menu.is_at_root());
    assert_eq!(menu.current_menu().title(), "Main Menu");
}

/// Read-only live game state owned by the application.
struct Game {
    in_progress: bool,
}

/// While a game is running, escape on the root offers to resign instead.
struct ResignOnEscape;

impl ExternalBehavior<Game, Action> for ResignOnEscape {
    fn on_input(
        &mut self,
        game: &Game,
        menu: MenuSnapshot<'_, Action>,
        input: Input,
    ) -> Option<Command<Action>> {
        (game.in_progress && input == Input::Escape && menu.depth() == 0)
            .then_some(Command::Action(Action::ResignGame))
    }
}

#[test]
fn live_game_state_changes_what_escape_means() {
    let mut menu = MenuState::new(&ROOT);
    let mut firmware = Recorder::default();
    let mut behavior = ResignOnEscape;
    let mut game = Game { in_progress: false };

    assert_eq!(
        menu.handle_with_and_dispatch(Input::Escape, &game, &mut behavior, &mut firmware),
        Event::Ignored
    );

    game.in_progress = true;
    assert_eq!(
        menu.handle_with_and_dispatch(Input::Escape, &game, &mut behavior, &mut firmware),
        Event::ExternalAction(Action::ResignGame)
    );

    // Inside a submenu escape keeps its normal meaning.
    let _ = menu.handle_with_and_dispatch(Input::Ok, &game, &mut behavior, &mut firmware);
    assert_eq!(
        menu.handle_with_and_dispatch(Input::Escape, &game, &mut behavior, &mut firmware),
        Event::Closed { depth: 0 }
    );
    assert_eq!(firmware.calls, [Call::Action(Action::ResignGame)]);
}

#[test]
fn renderer_can_draw_every_screen_from_snapshots_alone() {
    let mut menu = MenuState::new(&ROOT);
    let mut screens = Vec::new();

    for input in [Input::Down, Input::Ok, Input::Escape, Input::Up, Input::Ok] {
        let _ = menu.handle(input);
        let snapshot = menu.snapshot();
        let labels: Vec<_> = snapshot
            .menu()
            .items()
            .iter()
            .map(MenuItem::label)
            .collect();
        screens.push((snapshot.menu().title(), labels, snapshot.selected_index()));
    }

    assert_eq!(
        screens,
        [
            ("Main Menu", vec!["Play", "Settings"], 1),
            ("Settings", vec!["Sound"], 0),
            ("Main Menu", vec!["Play", "Settings"], 1),
            ("Main Menu", vec!["Play", "Settings"], 0),
            ("Play", vec!["Local", "Online"], 0),
        ]
    );
}
