use menu::{Command, Input, Menu, MenuControls, MenuItem};

/// An action named after where it is defined, so mismatches read clearly.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Act(pub &'static str);

/// Every operation a caller can perform on a `MenuState`.
#[derive(Clone, Copy, Debug)]
pub enum Op {
    Press(Input),
    Unblock,
}

pub const OPS: [Op; 7] = [
    Op::Press(Input::Up),
    Op::Press(Input::Down),
    Op::Press(Input::Left),
    Op::Press(Input::Right),
    Op::Press(Input::Ok),
    Op::Press(Input::Escape),
    Op::Unblock,
];

pub static ROOT: Menu<'static, Act> = Menu::new(
    "Root",
    &[
        MenuItem::action("Play", Act("root play")),
        MenuItem::submenu("Options", &OPTIONS),
        MenuItem::blocking_action("Sync", Act("root sync"), Act("root cancel sync")),
        MenuItem::submenu("Empty", &EMPTY),
        MenuItem::submenu("Tower", &TOWER),
    ],
);

/// Custom controls, a nested blocking entry and a link back to the root.
static OPTIONS: Menu<'static, Act> = Menu::with_controls(
    "Options",
    &[
        MenuItem::action("Sound", Act("options sound")),
        MenuItem::blocking_action("Pair", Act("options pair"), Act("options unpair")),
        MenuItem::submenu("Home", &ROOT),
    ],
    MenuControls::new(
        Command::SelectPrevious,
        Command::SelectNext,
        Command::Action(Act("options left")),
        Command::Ignore,
        Command::Activate,
        Command::GoBack,
    ),
);

/// No entries; escape is an action, so only left leaves.
static EMPTY: Menu<'static, Act> = Menu::with_controls(
    "Empty",
    &[],
    MenuControls::new(
        Command::SelectPrevious,
        Command::SelectNext,
        Command::GoBack,
        Command::Activate,
        Command::Activate,
        Command::Action(Act("empty escape")),
    ),
);

/// Opens itself and only escape goes back, so random walks climb to the limit.
static TOWER: Menu<'static, Act> = Menu::with_controls(
    "Tower",
    &[
        MenuItem::submenu("Up", &TOWER),
        MenuItem::blocking_action("Bell", Act("tower bell"), Act("tower silence")),
    ],
    MenuControls::new(
        Command::SelectPrevious,
        Command::SelectNext,
        Command::Activate,
        Command::Activate,
        Command::Activate,
        Command::GoBack,
    ),
);
