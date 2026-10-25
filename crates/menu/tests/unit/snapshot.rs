use menu::{Input, Menu, MenuItem, MenuSnapshot, MenuState};

use crate::common::{Action, ROOT, SETTINGS};

static OPERATIONS: Menu<'static, Action> = Menu::new(
    "Operations",
    &[MenuItem::blocking_action(
        "Connect",
        Action::Start,
        Action::CancelStart,
    )],
);

fn assert_mirrors(snapshot: MenuSnapshot<'_, Action>, state: &MenuState<'_, Action>) {
    assert!(core::ptr::eq(snapshot.menu(), state.current_menu()));
    assert_eq!(snapshot.selected_index(), state.selected_index());
    assert_eq!(snapshot.selected_item(), state.selected_item());
    assert_eq!(snapshot.depth(), state.depth());
    assert_eq!(snapshot.is_blocked(), state.is_blocked());
    assert_eq!(snapshot.blocking_action(), state.blocking_action());
    assert_eq!(
        snapshot.blocking_escape_action(),
        state.blocking_escape_action()
    );
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
    assert!(!snapshot.is_blocked());
}

#[test]
fn snapshot_follows_submenus() {
    let mut state = MenuState::new(&ROOT);
    let _ = state.handle(Input::Down);
    let _ = state.handle(Input::Right);
    let snapshot = state.snapshot();

    assert!(core::ptr::eq(snapshot.menu(), &raw const SETTINGS));
    assert_eq!(snapshot.depth(), 1);
    assert_mirrors(snapshot, &state);
}

#[test]
fn snapshot_reports_an_active_blocking_operation() {
    let mut state = MenuState::new(&OPERATIONS);
    let _ = state.handle(Input::Ok);
    let snapshot = state.snapshot();

    assert!(snapshot.is_blocked());
    assert_eq!(snapshot.blocking_action(), Some(&Action::Start));
    assert_eq!(
        snapshot.blocking_escape_action(),
        Some(&Action::CancelStart)
    );
    assert_mirrors(snapshot, &state);
}

#[test]
fn snapshot_of_an_empty_menu_has_no_selected_item() {
    let menu = Menu::<Action>::new("Empty", &[]);
    let state = MenuState::new(&menu);
    let snapshot = state.snapshot();

    assert_eq!(snapshot.selected_index(), 0);
    assert_eq!(snapshot.selected_item(), None);
}

#[test]
fn snapshot_is_a_copy_that_outlives_later_input() {
    let mut state = MenuState::new(&ROOT);
    let before = state.snapshot();
    let copy = before;

    let _ = state.handle(Input::Down);
    let _ = state.handle(Input::Right);

    assert_eq!(before.selected_index(), 0);
    assert_eq!(before.depth(), 0);
    assert_eq!(copy.selected_index(), before.selected_index());
    assert_mirrors(state.snapshot(), &state);
}
