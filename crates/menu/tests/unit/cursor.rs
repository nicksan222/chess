use menu::{Event, Input, Menu, MenuItem, MenuState};

use crate::common::{ALL_INPUTS, Action, press_all};

static THREE: Menu<'static, Action> = Menu::new(
    "Three",
    &[
        MenuItem::action("One", Action::Start),
        MenuItem::action("Two", Action::Wifi),
        MenuItem::action("Three", Action::ShowHelp),
    ],
);

#[test]
fn state_starts_on_the_first_entry_of_the_root() {
    let state = MenuState::new(&THREE);

    assert_eq!(state.selected_index(), 0);
    assert_eq!(state.selected_item().map(MenuItem::label), Some("One"));
    assert!(state.is_at_root());
    assert!(core::ptr::eq(state.root_menu(), &THREE));
}

#[test]
fn down_walks_every_entry_then_stops_at_the_last() {
    let mut state = MenuState::new(&THREE);

    assert_eq!(
        press_all(&mut state, &[Input::Down, Input::Down, Input::Down]),
        [
            Event::SelectionChanged { selected: 1 },
            Event::SelectionChanged { selected: 2 },
            Event::Ignored,
        ]
    );
    assert_eq!(state.selected_item().map(MenuItem::label), Some("Three"));
}

#[test]
fn up_walks_back_then_stops_at_the_first() {
    let mut state = MenuState::new(&THREE);
    let _ = press_all(&mut state, &[Input::Down, Input::Down]);

    assert_eq!(
        press_all(&mut state, &[Input::Up, Input::Up, Input::Up]),
        [
            Event::SelectionChanged { selected: 1 },
            Event::SelectionChanged { selected: 0 },
            Event::Ignored,
        ]
    );
}

#[test]
fn movement_never_wraps_around() {
    let mut state = MenuState::new(&THREE);

    assert_eq!(state.handle(Input::Up), Event::Ignored);
    assert_eq!(state.selected_index(), 0);

    let _ = press_all(&mut state, &[Input::Down; 10]);
    assert_eq!(state.selected_index(), 2);
}

#[test]
fn single_entry_menu_cannot_move() {
    let items = [MenuItem::action("Only", Action::Start)];
    let menu = Menu::new("One", &items);
    let mut state = MenuState::new(&menu);

    assert_eq!(state.handle(Input::Up), Event::Ignored);
    assert_eq!(state.handle(Input::Down), Event::Ignored);
    assert_eq!(state.handle(Input::Ok), Event::Activated(&Action::Start));
}

#[test]
fn activating_moves_nothing_and_can_repeat() {
    let mut state = MenuState::new(&THREE);
    let _ = state.handle(Input::Down);

    for _ in 0..3 {
        assert_eq!(state.handle(Input::Ok), Event::Activated(&Action::Wifi));
        assert_eq!(state.selected_index(), 1);
    }
}

#[test]
fn empty_menu_ignores_every_input() {
    let menu = Menu::<Action>::new("Empty", &[]);
    let mut state = MenuState::new(&menu);

    for input in ALL_INPUTS {
        assert_eq!(state.handle(input), Event::Ignored, "{input:?}");
    }
    assert_eq!(state.selected_index(), 0);
    assert_eq!(state.selected_item(), None);
}

#[test]
fn control_bound_action_does_not_move_the_cursor() {
    use crate::common::ROOT;

    let mut state = MenuState::new(&ROOT);
    let _ = state.handle(Input::Down);

    assert_eq!(state.handle(Input::Ok), Event::Activated(&Action::ShowHelp));
    assert_eq!(state.selected_index(), 1);
    assert!(state.is_at_root());
}

#[test]
fn state_can_be_created_in_const_context() {
    static STATE_ROOT: Menu<'static, Action> = Menu::new("Root", &[]);
    const fn initial() -> MenuState<'static, Action> {
        MenuState::new(&STATE_ROOT)
    }

    assert_eq!(initial().depth(), 0);
}
