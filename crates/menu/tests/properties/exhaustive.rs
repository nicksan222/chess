use menu::MenuState;

use crate::fixture::{OPS, Op, ROOT};
use crate::reference::Reference;

/// Every sequence of this many operations is checked: 7^6 = 117,649 runs.
const LENGTH: u32 = 6;

#[test]
fn every_short_operation_sequence_matches_the_reference() {
    let total = OPS.len().pow(LENGTH);

    for index in 0..total {
        let sequence = sequence_for(index);
        let mut state = MenuState::new(&ROOT);
        let mut reference = Reference::new(&ROOT);

        for (step, op) in sequence.iter().enumerate() {
            let context = format!("{sequence:?}, step {step}");
            match *op {
                Op::Press(input) => {
                    assert_eq!(state.handle(input), reference.press(input), "{context}");
                }
                Op::Unblock => assert_eq!(state.unblock(), reference.unblock(), "{context}"),
            }
            reference.assert_matches(&state, &context);
        }
    }
}

/// Decodes `index` as a base-7 number, one digit per operation.
fn sequence_for(mut index: usize) -> Vec<Op> {
    (0..LENGTH)
        .map(|_| {
            let op = OPS[index % OPS.len()];
            index /= OPS.len();
            op
        })
        .collect()
}
