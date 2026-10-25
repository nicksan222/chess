use menu::{Menu, MenuItem};

use crate::common::Action;

static CHILD: Menu<'static, Action> = Menu::new("Child", &[]);

#[test]
fn action_entry_exposes_its_label_and_action_only() {
    let item = MenuItem::action("Start", Action::Start);

    assert_eq!(item.label(), "Start");
    assert_eq!(item.as_action(), Some(&Action::Start));
    assert_eq!(item.escape_action(), None);
    assert_eq!(item.as_submenu(), None);
    assert!(!item.is_blocking());
}

#[test]
fn blocking_entry_exposes_its_start_and_escape_actions() {
    let item = MenuItem::blocking_action("Connect", Action::Start, Action::CancelStart);

    assert_eq!(item.label(), "Connect");
    assert_eq!(item.as_action(), Some(&Action::Start));
    assert_eq!(item.escape_action(), Some(&Action::CancelStart));
    assert_eq!(item.as_submenu(), None);
    assert!(item.is_blocking());
}

#[test]
fn submenu_entry_exposes_the_exact_child_menu() {
    let item = MenuItem::submenu("More", &CHILD);

    assert_eq!(item.label(), "More");
    assert_eq!(item.as_action(), None);
    assert_eq!(item.escape_action(), None);
    assert!(!item.is_blocking());
    assert!(
        item.as_submenu()
            .is_some_and(|menu| core::ptr::eq(menu, &raw const CHILD))
    );
}

#[test]
fn constructors_build_the_matching_variants() {
    assert_eq!(
        MenuItem::action("A", Action::Wifi),
        MenuItem::Action {
            label: "A",
            action: Action::Wifi,
        }
    );
    assert_eq!(
        MenuItem::blocking_action("B", Action::Start, Action::CancelStart),
        MenuItem::BlockingAction {
            label: "B",
            action: Action::Start,
            escape_action: Action::CancelStart,
        }
    );
    assert_eq!(
        MenuItem::submenu("C", &CHILD),
        MenuItem::Submenu {
            label: "C",
            menu: &CHILD,
        }
    );
}

#[test]
fn labels_are_kept_verbatim() {
    for label in [
        "",
        " ",
        "Échecs ♞",
        "a very long label that a renderer must clip",
    ] {
        assert_eq!(MenuItem::action(label, Action::Start).label(), label);
    }
}

#[test]
fn entries_can_be_built_in_const_context() {
    const ITEM: MenuItem<'static, Action> = MenuItem::action("Help", Action::ShowHelp);
    const LABEL: &str = ITEM.label();
    const { assert!(!ITEM.is_blocking()) };

    assert_eq!(LABEL, "Help");
}
