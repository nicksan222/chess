use std::{cell::Cell, rc::Rc};

use chess_core::{array_stack, collections::ArrayStack};

fn pop_order<T: Copy, const N: usize>(stack: &ArrayStack<T, N>) -> Vec<T> {
    stack.iter().copied().collect()
}

#[test]
fn new_stack_is_empty_with_fixed_capacity() {
    let stack = ArrayStack::<i32, 4>::new();

    assert!(stack.is_empty());
    assert!(!stack.is_full());
    assert_eq!(stack.len(), 0);
    assert_eq!(stack.capacity(), 4);
    assert_eq!(ArrayStack::<i32, 4>::CAPACITY, 4);
    assert_eq!(stack.peek(), None);
    assert_eq!(stack.bottom(), None);
}

#[test]
fn zero_capacity_stack_returns_rejected_element() {
    let mut stack = ArrayStack::<String, 0>::new();

    let error = stack
        .try_push(String::from("move"))
        .expect_err("zero-capacity stack is full");

    assert_eq!(error.into_element(), "move");
    assert!(stack.is_empty());
    assert!(stack.is_full());
    assert_eq!(stack.pop(), None);
}

#[test]
fn push_and_pop_follow_lifo_order_without_overwriting() {
    let mut stack = ArrayStack::<_, 3>::new();

    stack.try_push(1).expect("space available");
    stack.try_push(2).expect("space available");
    stack.try_push(3).expect("space available");
    let error = stack.try_push(4).expect_err("stack is full");

    assert_eq!(error.into_element(), 4);
    assert_eq!(pop_order(&stack), [3, 2, 1]);
    assert_eq!(stack.pop(), Some(3));
    assert_eq!(stack.pop(), Some(2));
    assert_eq!(stack.pop(), Some(1));
    assert_eq!(stack.pop(), None);
}

#[test]
fn mutable_access_and_iteration_follow_pop_order() {
    let mut stack = array_stack![1, 2, 3];

    *stack.peek_mut().expect("top exists") = 30;
    *stack.bottom_mut().expect("bottom exists") = 10;

    let mut visited = Vec::new();
    for element in &mut stack {
        visited.push(*element);
        *element += 1;
    }

    assert_eq!(visited, [30, 2, 10]);
    assert_eq!(pop_order(&stack), [31, 3, 11]);
}

#[test]
fn truncate_removes_only_elements_above_requested_length() {
    let mut stack = array_stack![1, 2, 3, 4];

    stack.truncate(2);
    assert_eq!(pop_order(&stack), [2, 1]);

    stack.truncate(8);
    assert_eq!(pop_order(&stack), [2, 1]);
}

#[test]
fn macro_supports_all_forms_and_evaluates_left_to_right() {
    let empty: ArrayStack<u8, 0> = array_stack![];
    let order = Cell::new(0);
    let next = || {
        let value = order.get();
        order.set(value + 1);
        value
    };

    let elements = array_stack![next(), next(), next(),];
    let repeated = array_stack![String::from("move"); 3];

    assert!(empty.is_empty());
    assert_eq!(pop_order(&elements), [2, 1, 0]);
    assert_eq!(order.get(), 3);
    assert_eq!(
        repeated.into_iter().collect::<Vec<_>>(),
        ["move", "move", "move"]
    );
}

#[test]
fn clone_comparison_debug_and_consuming_iteration_use_pop_order() {
    let stack = array_stack![1, 2, 3];
    let clone = stack.clone();

    assert_eq!(stack, clone);
    assert!(stack < array_stack![1, 2, 4]);
    assert_eq!(format!("{stack:?}"), "[3, 2, 1]");
    assert_eq!(clone.into_iter().collect::<Vec<_>>(), [3, 2, 1]);
}

#[test]
fn clear_drops_each_element_once_and_allows_reuse() {
    struct DropCounter(Rc<Cell<usize>>);

    impl Drop for DropCounter {
        fn drop(&mut self) {
            self.0.set(self.0.get() + 1);
        }
    }

    let drops = Rc::new(Cell::new(0));
    let mut stack = ArrayStack::<_, 4>::new();
    for _ in 0..4 {
        stack
            .try_push(DropCounter(Rc::clone(&drops)))
            .unwrap_or_else(|_| panic!("space available"));
    }

    stack.clear();
    assert_eq!(drops.get(), 4);
    assert!(stack.is_empty());

    stack
        .try_push(DropCounter(Rc::clone(&drops)))
        .unwrap_or_else(|_| panic!("space available"));
    drop(stack);
    assert_eq!(drops.get(), 5);
}

#[test]
fn operation_sequence_matches_bounded_vec_model() {
    const CAPACITY: usize = 7;
    let mut stack = ArrayStack::<i32, CAPACITY>::new();
    let mut model = Vec::new();
    let mut state = 0xCAFE_BABE_u32;

    for _ in 0..10_000 {
        state = state.wrapping_mul(1_664_525).wrapping_add(1_013_904_223);
        match state % 3 {
            0 | 1 => {
                let value = state as i32;
                let actual = stack.try_push(value).map_err(|error| error.into_element());
                let expected = if model.len() == CAPACITY {
                    Err(value)
                } else {
                    model.push(value);
                    Ok(())
                };
                assert_eq!(actual, expected);
            }
            _ => assert_eq!(stack.pop(), model.pop()),
        }

        assert_eq!(stack.len(), model.len());
        assert_eq!(stack.peek(), model.last());
        assert_eq!(stack.bottom(), model.first());
        assert_eq!(
            stack.iter().copied().collect::<Vec<_>>(),
            model.iter().rev().copied().collect::<Vec<_>>()
        );
    }
}
