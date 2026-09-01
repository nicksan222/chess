use std::cell::Cell;

use logger::info;

#[test]
fn logging_is_a_no_op_before_registration() {
    let evaluations = Cell::new(0);

    info!("unused {}", {
        evaluations.set(evaluations.get() + 1);
        7
    });

    assert!(logger::get().is_none());
    assert_eq!(evaluations.get(), 0);
}
