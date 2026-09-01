use menu::{Command, Input, Menu, MenuControls, MenuDefinition, MenuItem};

use crate::common::{Action, ROOT};

fn title_of<'a, D>(menu: &D) -> &'a str
where
    D: MenuDefinition<'a, Action>,
{
    menu.title()
}

#[test]
fn menu_definition_exposes_renderer_data() {
    assert_eq!(title_of(&ROOT), "Chess");
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
fn conventional_controls_define_a_vertical_list() {
    let controls = MenuControls::<Action>::list();

    assert_eq!(controls.command(Input::Up), &Command::SelectPrevious);
    assert_eq!(controls.command(Input::Down), &Command::SelectNext);
    assert_eq!(controls.command(Input::Left), &Command::GoBack);
    assert_eq!(controls.command(Input::Right), &Command::Activate);
    assert_eq!(controls.command(Input::Ok), &Command::Activate);
}

#[test]
fn empty_menu_has_no_items() {
    let menu = Menu::<Action>::new("Empty", &[]);

    assert!(menu.is_empty());
    assert_eq!(menu.items(), &[] as &[MenuItem<'_, Action>]);
}
