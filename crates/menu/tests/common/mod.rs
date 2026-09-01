use menu::{Command, Menu, MenuControls, MenuItem};

#[derive(Debug, Eq, PartialEq)]
pub enum Action {
    Start,
    Wifi,
    DecreaseVolume,
    IncreaseVolume,
    ShowHelp,
}

pub static SETTINGS: Menu<'static, Action> = Menu::with_controls(
    "Settings",
    &[MenuItem::action("WiFi", Action::Wifi)],
    MenuControls::new(
        Command::SelectPrevious,
        Command::SelectNext,
        Command::Action(Action::DecreaseVolume),
        Command::Action(Action::IncreaseVolume),
        Command::Activate,
    ),
);

pub static ROOT: Menu<'static, Action> = Menu::with_controls(
    "Chess",
    &[
        MenuItem::action("Start", Action::Start),
        MenuItem::submenu("Settings", &SETTINGS),
    ],
    MenuControls::new(
        Command::SelectPrevious,
        Command::SelectNext,
        Command::Ignore,
        Command::Activate,
        Command::Action(Action::ShowHelp),
    ),
);
