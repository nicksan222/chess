use menu::{Event, Input, MAX_MENU_DEPTH, Menu, MenuItem, MenuState};

use crate::common::{Action, ROOT, SETTINGS, is_showing};

static LEVEL_9: Menu<'static, Action> = Menu::new("9", &[]);
static LEVEL_8: Menu<'static, Action> = Menu::new("8", &[MenuItem::submenu("9", &LEVEL_9)]);
static LEVEL_7: Menu<'static, Action> = Menu::new("7", &[MenuItem::submenu("8", &LEVEL_8)]);
static LEVEL_6: Menu<'static, Action> = Menu::new("6", &[MenuItem::submenu("7", &LEVEL_7)]);
static LEVEL_5: Menu<'static, Action> = Menu::new("5", &[MenuItem::submenu("6", &LEVEL_6)]);
static LEVEL_4: Menu<'static, Action> = Menu::new("4", &[MenuItem::submenu("5", &LEVEL_5)]);
static LEVEL_3: Menu<'static, Action> = Menu::new("3", &[MenuItem::submenu("4", &LEVEL_4)]);
static LEVEL_2: Menu<'static, Action> = Menu::new("2", &[MenuItem::submenu("3", &LEVEL_3)]);
static LEVEL_1: Menu<'static, Action> = Menu::new("1", &[MenuItem::submenu("2", &LEVEL_2)]);
static LEVEL_0: Menu<'static, Action> = Menu::new("0", &[MenuItem::submenu("1", &LEVEL_1)]);

/// A menu whose second entry opens itself, so any depth can be reached while
/// every level has a distinct cursor position to restore.
static RECURSIVE: Menu<'static, Action> = Menu::new(
    "Recursive",
    &[
        MenuItem::action("Stay", Action::Start),
        MenuItem::submenu("Deeper", &RECURSIVE),
        MenuItem::action("Also stay", Action::Wifi),
    ],
);

#[test]
fn opening_a_submenu_shows_it_from_its_first_entry() {
    let mut state = MenuState::new(&ROOT);
    let _ = state.handle(Input::Down);

    assert_eq!(state.handle(Input::Right), Event::Opened { depth: 1 });
    assert!(is_showing(&state, &SETTINGS));
    assert_eq!(state.selected_index(), 0);
    assert_eq!(state.depth(), 1);
    assert!(!state.is_at_root());
    assert!(core::ptr::eq(state.root_menu(), &ROOT));
}

#[test]
fn each_menu_uses_its_own_controls() {
    let mut state = MenuState::new(&ROOT);

    assert_eq!(state.handle(Input::Ok), Event::Activated(&Action::ShowHelp));
    assert_eq!(state.handle(Input::Left), Event::Ignored);

    let _ = state.handle(Input::Down);
    assert_eq!(state.handle(Input::Right), Event::Opened { depth: 1 });
    assert_eq!(state.current_menu().title(), "Settings");
    assert_eq!(
        state.handle(Input::Left),
        Event::Activated(&Action::DecreaseVolume)
    );
    assert_eq!(
        state.handle(Input::Right),
        Event::Activated(&Action::IncreaseVolume)
    );
}

#[test]
fn returning_to_a_parent_restores_its_cursor() {
    let child = Menu::new("Child", &[]);
    let items = [
        MenuItem::action("First", Action::Start),
        MenuItem::submenu("Child", &child),
    ];
    let root = Menu::new("Root", &items);
    let mut state = MenuState::new(&root);
    let _ = state.handle(Input::Down);

    assert_eq!(state.handle(Input::Ok), Event::Opened { depth: 1 });
    assert_eq!(state.handle(Input::Left), Event::Closed { depth: 0 });
    assert_eq!(state.selected_index(), 1);
    assert!(state.is_at_root());
    assert!(is_showing(&state, &root));
}

#[test]
fn reopening_a_submenu_does_not_remember_its_old_cursor() {
    let mut state = MenuState::new(&RECURSIVE);
    let _ = state.handle(Input::Down);
    let _ = state.handle(Input::Ok);
    let _ = state.handle(Input::Down);
    let _ = state.handle(Input::Down);
    assert_eq!(state.selected_index(), 2);

    assert_eq!(state.handle(Input::Escape), Event::Closed { depth: 0 });
    assert_eq!(state.handle(Input::Ok), Event::Opened { depth: 1 });
    assert_eq!(state.selected_index(), 0);
}

#[test]
fn going_back_at_the_root_is_ignored() {
    let mut state = MenuState::new(&LEVEL_0);

    assert_eq!(state.handle(Input::Left), Event::Ignored);
    assert_eq!(state.handle(Input::Escape), Event::Ignored);
    assert!(state.is_at_root());
}

#[test]
fn navigation_reports_the_fixed_depth_limit() {
    let mut state = MenuState::new(&LEVEL_0);

    for expected_depth in 1..=MAX_MENU_DEPTH {
        assert_eq!(
            state.handle(Input::Ok),
            Event::Opened {
                depth: expected_depth
            }
        );
    }

    assert_eq!(state.handle(Input::Ok), Event::DepthLimitReached);
    assert_eq!(state.depth(), MAX_MENU_DEPTH);
    assert_eq!(state.current_menu().title(), "8");
}

#[test]
fn reaching_the_depth_limit_changes_nothing_and_is_repeatable() {
    let mut state = MenuState::new(&RECURSIVE);
    let _ = state.handle(Input::Down);
    for _ in 0..MAX_MENU_DEPTH {
        let _ = state.handle(Input::Ok);
        let _ = state.handle(Input::Down);
    }

    for _ in 0..3 {
        assert_eq!(state.handle(Input::Ok), Event::DepthLimitReached);
        assert_eq!(state.depth(), MAX_MENU_DEPTH);
        assert_eq!(state.selected_index(), 1);
    }
}

#[test]
fn depth_limit_is_eight() {
    assert_eq!(MAX_MENU_DEPTH, 8);
}

#[test]
fn every_level_restores_its_own_cursor_on_the_way_back() {
    let mut state = MenuState::new(&RECURSIVE);
    let _ = state.handle(Input::Down);

    // Leave each level with the cursor on "Deeper" (index 1) and, once open,
    // park the deepest level on its last entry (index 2).
    for depth in 1..=MAX_MENU_DEPTH {
        assert_eq!(state.handle(Input::Ok), Event::Opened { depth });
        let _ = state.handle(Input::Down);
    }
    let _ = state.handle(Input::Down);
    assert_eq!(state.selected_index(), 2);

    for depth in (0..MAX_MENU_DEPTH).rev() {
        assert_eq!(state.handle(Input::Left), Event::Closed { depth });
        assert_eq!(state.selected_index(), 1, "depth {depth}");
    }
    assert!(state.is_at_root());
    assert_eq!(state.handle(Input::Left), Event::Ignored);
}

#[test]
fn history_is_reusable_after_returning_to_the_root() {
    let mut state = MenuState::new(&LEVEL_0);

    for _round in 0..3 {
        for depth in 1..=MAX_MENU_DEPTH {
            assert_eq!(state.handle(Input::Ok), Event::Opened { depth });
        }
        assert_eq!(state.handle(Input::Ok), Event::DepthLimitReached);
        for depth in (0..MAX_MENU_DEPTH).rev() {
            assert_eq!(state.handle(Input::Escape), Event::Closed { depth });
        }
        assert!(is_showing(&state, &LEVEL_0));
    }
}

#[test]
fn a_cyclic_tree_is_bounded_by_the_depth_limit() {
    static PING: Menu<'static, Action> = Menu::new("Ping", &[MenuItem::submenu("Pong", &PONG)]);
    static PONG: Menu<'static, Action> = Menu::new("Pong", &[MenuItem::submenu("Ping", &PING)]);
    let mut state = MenuState::new(&PING);

    for depth in 1..=MAX_MENU_DEPTH {
        assert_eq!(state.handle(Input::Ok), Event::Opened { depth });
        let expected: &Menu<'_, Action> = if depth % 2 == 0 { &PING } else { &PONG };
        assert!(is_showing(&state, expected), "depth {depth}");
    }
    assert_eq!(state.handle(Input::Ok), Event::DepthLimitReached);
}
