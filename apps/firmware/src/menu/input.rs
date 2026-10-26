//! Product bindings from physical panel labels to menu inputs.

use crate::hardware::pins::Button;

/// The application's menu binding for a physical control-panel label.
pub(crate) fn input(button: Button) -> Option<::menu::Input> {
    use ::menu::Input;
    match button {
        Button::Up => Some(Input::Up),
        Button::Down => Some(Input::Down),
        Button::Left => Some(Input::Left),
        Button::Right => Some(Input::Right),
        Button::Ok => Some(Input::Ok),
        Button::Reset
        | Button::Pass
        | Button::F1
        | Button::F2
        | Button::F3
        | Button::F4
        | Button::F5 => None,
    }
}

#[cfg(test)]
mod tests {
    use super::input;
    use crate::hardware::pins::Button;
    use ::menu::Input;

    #[test]
    fn panel_bindings_preserve_navigation_and_leave_other_controls_unassigned() {
        for (button, expected) in [
            (Button::Up, Some(Input::Up)),
            (Button::Down, Some(Input::Down)),
            (Button::Left, Some(Input::Left)),
            (Button::Right, Some(Input::Right)),
            (Button::Ok, Some(Input::Ok)),
            (Button::Reset, None),
            (Button::Pass, None),
            (Button::F1, None),
            (Button::F2, None),
            (Button::F3, None),
            (Button::F4, None),
            (Button::F5, None),
        ] {
            assert_eq!(input(button), expected, "{button:?}");
        }
    }
}
