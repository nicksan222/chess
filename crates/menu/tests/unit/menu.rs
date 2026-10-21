use menu::{Command, Input, Menu, MenuControls, MenuDefinition, MenuItem};

use crate::common::{Action, ROOT, SETTINGS};

fn title_of<'a, D>(menu: &D) -> &'a str
where
    D: MenuDefinition<'a, Action>,
{
    menu.title()
}

#[test]
fn menu_exposes_renderer_data() {
    assert_eq!(ROOT.title(), "Chess");
    assert_eq!(ROOT.items().len(), 2);
    assert_eq!(ROOT.items()[0].label(), "Start");
    assert_eq!(ROOT.items()[0].as_action(), Some(&Action::Start));
    assert_eq!(
        ROOT.items()[1].as_submenu().map(Menu::title),
        Some("Settings")
    );
    assert!(!ROOT.is_empty());
}

#[test]
fn menu_definition_trait_matches_inherent_accessors() {
    assert_eq!(title_of(&ROOT), ROOT.title());
    assert_eq!(MenuDefinition::items(&ROOT), ROOT.items());
    assert_eq!(MenuDefinition::controls(&SETTINGS), SETTINGS.controls());
}

#[test]
fn new_menu_uses_conventional_list_controls() {
    let menu = Menu::<Action>::new("List", &[]);

    assert_eq!(menu.controls(), &MenuControls::list());
}

#[test]
fn explicit_controls_are_kept_per_menu() {
    assert_eq!(
        SETTINGS.controls().command(Input::Left),
        &Command::Action(Action::DecreaseVolume)
    );
    assert_eq!(ROOT.controls().command(Input::Left), &Command::Ignore);
}

#[test]
fn items_keep_definition_order() {
    let items = [
        MenuItem::action("First", Action::Start),
        MenuItem::action("Second", Action::Wifi),
        MenuItem::action("Third", Action::ShowHelp),
    ];
    let menu = Menu::new("Ordered", &items);

    let labels: Vec<_> = menu.items().iter().map(MenuItem::label).collect();
    assert_eq!(labels, ["First", "Second", "Third"]);
}

#[test]
fn empty_menu_has_no_items() {
    let menu = Menu::<Action>::new("Empty", &[]);

    assert!(menu.is_empty());
    assert_eq!(menu.items(), &[] as &[MenuItem<'_, Action>]);
}

#[test]
fn menus_may_reference_each_other_in_a_cycle() {
    static PING: Menu<'static, Action> = Menu::new("Ping", &[MenuItem::submenu("Pong", &PONG)]);
    static PONG: Menu<'static, Action> = Menu::new("Pong", &[MenuItem::submenu("Ping", &PING)]);

    let pong = PING.items()[0].as_submenu().expect("ping links to pong");
    let ping = pong.items()[0].as_submenu().expect("pong links to ping");
    assert!(core::ptr::eq(ping, &PING));
}
