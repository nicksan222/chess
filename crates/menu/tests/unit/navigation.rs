use menu::{Event, Input, Menu, MenuItem, MenuState};

use crate::common::{Action, ROOT};

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

#[test]
fn movement_is_bounded_and_does_not_wrap() {
    let items = [
        MenuItem::action("One", Action::Start),
        MenuItem::action("Two", Action::Wifi),
    ];
    let menu = Menu::new("List", &items);
    let mut state = MenuState::new(&menu);

    assert_eq!(state.handle(Input::Up), Event::Ignored);
    assert_eq!(
        state.handle(Input::Down),
        Event::SelectionChanged { selected: 1 }
    );
    assert_eq!(state.handle(Input::Down), Event::Ignored);
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
}

#[test]
fn empty_menu_ignores_navigation_and_activation() {
    let menu = Menu::<Action>::new("Empty", &[]);
    let mut state = MenuState::new(&menu);

    assert_eq!(state.selected_item(), None);
    assert_eq!(state.handle(Input::Down), Event::Ignored);
    assert_eq!(state.handle(Input::Ok), Event::Ignored);
    assert_eq!(state.handle(Input::Left), Event::Ignored);
}

#[test]
fn snapshot_is_a_read_only_view_of_current_state() {
    let mut state = MenuState::new(&ROOT);
    let _ = state.handle(Input::Down);
    let snapshot = state.snapshot();

    assert_eq!(snapshot.menu().title(), "Chess");
    assert_eq!(snapshot.selected_index(), 1);
    assert_eq!(
        snapshot.selected_item().map(MenuItem::label),
        Some("Settings")
    );
    assert_eq!(snapshot.depth(), 0);
}

#[test]
fn navigation_reports_the_fixed_depth_limit() {
    let mut state = MenuState::new(&LEVEL_0);

    for expected_depth in 1..=8 {
        assert_eq!(
            state.handle(Input::Ok),
            Event::Opened {
                depth: expected_depth
            }
        );
    }

    assert_eq!(state.handle(Input::Ok), Event::DepthLimitReached);
    assert_eq!(state.depth(), 8);
    assert_eq!(state.current_menu().title(), "8");
}
