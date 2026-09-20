use firmware::hardware::pins::{Button, ButtonEvent};
use firmware::hardware::{BoardPosition, HardwareEvent, PieceEvent};

const BUTTONS: [Button; 12] = [
    Button::Up,
    Button::Down,
    Button::Left,
    Button::Right,
    Button::Ok,
    Button::Reset,
    Button::Pass,
    Button::F1,
    Button::F2,
    Button::F3,
    Button::F4,
    Button::F5,
];

#[test]
fn every_button_and_transition_converts_to_a_hardware_event() {
    for button in BUTTONS {
        for event in [ButtonEvent::Pressed(button), ButtonEvent::Released(button)] {
            assert_eq!(HardwareEvent::from(event), HardwareEvent::Button(event));
        }
    }
}

#[test]
fn every_board_position_round_trips_through_piece_events() {
    for row in 0..BoardPosition::SIZE {
        for column in 0..BoardPosition::SIZE {
            let position = BoardPosition::new(row, column).unwrap();
            assert_eq!(position.row(), row);
            assert_eq!(position.column(), column);

            for event in [PieceEvent::Placed(position), PieceEvent::Removed(position)] {
                assert_eq!(event.position(), position);
                assert_eq!(HardwareEvent::from(event), HardwareEvent::Piece(event));
            }
        }
    }
}

#[test]
fn positions_outside_either_grid_axis_are_rejected() {
    for coordinate in BoardPosition::SIZE..=u8::MAX {
        assert_eq!(BoardPosition::new(coordinate, 0), None);
        assert_eq!(BoardPosition::new(0, coordinate), None);
        assert_eq!(BoardPosition::new(coordinate, coordinate), None);
    }
}
