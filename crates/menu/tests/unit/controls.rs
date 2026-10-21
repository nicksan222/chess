use menu::{Command, Input, MenuControls};

use crate::common::{ALL_INPUTS, Action};

#[test]
fn conventional_controls_define_a_vertical_list() {
    let controls = MenuControls::<Action>::list();

    assert_eq!(controls.command(Input::Up), &Command::SelectPrevious);
    assert_eq!(controls.command(Input::Down), &Command::SelectNext);
    assert_eq!(controls.command(Input::Left), &Command::GoBack);
    assert_eq!(controls.command(Input::Right), &Command::Activate);
    assert_eq!(controls.command(Input::Ok), &Command::Activate);
    assert_eq!(controls.command(Input::Escape), &Command::GoBack);
}

#[test]
fn default_controls_are_the_conventional_list() {
    assert_eq!(MenuControls::<Action>::default(), MenuControls::list());
}

#[test]
fn every_input_reads_its_own_binding() {
    let controls = MenuControls::new(
        Command::Action(Action::Start),
        Command::Action(Action::CancelStart),
        Command::Action(Action::Wifi),
        Command::Action(Action::DecreaseVolume),
        Command::Action(Action::IncreaseVolume),
        Command::Action(Action::ShowHelp),
    );
    let expected = [
        Action::Start,
        Action::CancelStart,
        Action::Wifi,
        Action::DecreaseVolume,
        Action::IncreaseVolume,
        Action::ShowHelp,
    ];

    for (input, action) in ALL_INPUTS.into_iter().zip(expected) {
        assert_eq!(
            controls.command(input),
            &Command::Action(action),
            "{input:?}"
        );
    }
}

#[test]
fn every_input_can_be_deliberately_ignored() {
    let controls = MenuControls::<Action>::new(
        Command::Ignore,
        Command::Ignore,
        Command::Ignore,
        Command::Ignore,
        Command::Ignore,
        Command::Ignore,
    );

    for input in ALL_INPUTS {
        assert_eq!(controls.command(input), &Command::Ignore, "{input:?}");
    }
}

#[test]
fn controls_can_be_built_in_const_context() {
    const CONTROLS: MenuControls<Action> = MenuControls::list();

    assert_eq!(CONTROLS.command(Input::Ok), &Command::Activate);
}
