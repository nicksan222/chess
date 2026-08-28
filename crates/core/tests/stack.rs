use std::{
    cell::Cell,
    collections::hash_map::DefaultHasher,
    hash::{Hash, Hasher},
};

use chess_core::{collections::Stack, stack};

fn pop_order<T: Copy>(stack: &Stack<T>) -> Vec<T> {
    stack.iter().copied().collect()
}

#[test]
fn new_stack_is_empty_without_capacity() {
    let stack = Stack::<i32>::new();

    assert!(stack.is_empty());
    assert_eq!(stack.len(), 0);
    assert_eq!(stack.capacity(), 0);
    assert_eq!(stack.peek(), None);
    assert_eq!(stack.bottom(), None);
}

#[test]
fn push_and_pop_follow_lifo_order() {
    let mut stack = Stack::new();

    stack.push(1);
    stack.push(2);
    stack.push(3);

    assert_eq!(stack.len(), 3);
    assert_eq!(stack.peek(), Some(&3));
    assert_eq!(stack.bottom(), Some(&1));
    assert_eq!(stack.pop(), Some(3));
    assert_eq!(stack.pop(), Some(2));
    assert_eq!(stack.pop(), Some(1));
    assert_eq!(stack.pop(), None);
    assert!(stack.is_empty());
}

#[test]
fn mutable_access_and_iteration_follow_pop_order() {
    let mut stack = stack![1, 2, 3];

    *stack.peek_mut().expect("top exists") = 30;
    *stack.bottom_mut().expect("bottom exists") = 10;

    let mut visited = Vec::new();
    for value in &mut stack {
        visited.push(*value);
        *value += 1;
    }

    assert_eq!(visited, [30, 2, 10]);
    assert_eq!(pop_order(&stack), [31, 3, 11]);
}

#[test]
fn append_places_source_above_destination_and_empties_source() {
    let mut lower = stack![1, 2];
    let mut upper = stack![3, 4];

    lower.append(&mut upper);

    assert_eq!(pop_order(&lower), [4, 3, 2, 1]);
    assert!(upper.is_empty());
}

#[test]
fn truncate_removes_elements_from_the_top() {
    let mut stack = stack![1, 2, 3, 4];

    stack.truncate(2);
    assert_eq!(pop_order(&stack), [2, 1]);

    stack.truncate(10);
    assert_eq!(pop_order(&stack), [2, 1]);
}

#[test]
fn capacity_can_be_managed_without_changing_elements() {
    let mut stack = Stack::with_capacity(2);
    stack.extend([1, 2]);
    let old_capacity = stack.capacity();

    stack.reserve(10);
    assert!(stack.capacity() >= stack.len() + 10);
    assert!(stack.capacity() >= old_capacity);
    assert_eq!(pop_order(&stack), [2, 1]);

    stack.shrink_to_fit();
    assert!(stack.capacity() >= stack.len());
    assert_eq!(pop_order(&stack), [2, 1]);
}

#[test]
fn failed_reservation_leaves_stack_unchanged() {
    let mut stack = stack![1, 2, 3];
    let capacity = stack.capacity();

    assert!(stack.try_reserve(usize::MAX).is_err());
    assert_eq!(stack.capacity(), capacity);
    assert_eq!(pop_order(&stack), [3, 2, 1]);
}

#[test]
fn construction_conversion_and_extension_preserve_push_order() {
    let mut stack = Stack::from([1, 2]);
    stack.extend([3, 4]);
    stack.extend(&[5, 6]);

    let storage: Vec<_> = stack.clone().into();
    let round_trip = Stack::from(storage);

    assert_eq!(pop_order(&stack), [6, 5, 4, 3, 2, 1]);
    assert_eq!(round_trip, stack);
    assert_eq!(
        stack.clone().into_iter().collect::<Vec<_>>(),
        [6, 5, 4, 3, 2, 1]
    );
    assert_eq!(format!("{stack:?}"), "[6, 5, 4, 3, 2, 1]");
}

#[test]
fn comparison_and_hash_use_stack_sequence_semantics() {
    let lower_top = stack![9, 1];
    let higher_top = stack![0, 2];
    let clone = lower_top.clone();

    assert!(lower_top < higher_top);
    assert_eq!(lower_top, clone);

    let mut original_hash = DefaultHasher::new();
    let mut clone_hash = DefaultHasher::new();
    lower_top.hash(&mut original_hash);
    clone.hash(&mut clone_hash);
    assert_eq!(original_hash.finish(), clone_hash.finish());
}

#[test]
fn clear_retains_storage_for_reuse() {
    let mut stack = Stack::with_capacity(8);
    stack.extend(0..8);
    let capacity = stack.capacity();

    stack.clear();
    assert!(stack.is_empty());
    assert_eq!(stack.capacity(), capacity);

    stack.extend([10, 11]);
    assert_eq!(pop_order(&stack), [11, 10]);
}

#[test]
fn macro_supports_all_forms_and_evaluates_left_to_right() {
    let empty: Stack<u8> = stack![];
    let order = Cell::new(0);
    let next = || {
        let value = order.get();
        order.set(value + 1);
        value
    };

    let elements = stack![next(), next(), next(),];
    let repeated = stack![String::from("move"); 3];

    assert!(empty.is_empty());
    assert_eq!(pop_order(&elements), [2, 1, 0]);
    assert_eq!(order.get(), 3);
    assert_eq!(
        repeated.into_iter().collect::<Vec<_>>(),
        ["move", "move", "move"]
    );
}

#[test]
fn operation_sequence_matches_vec_model() {
    let mut stack = Stack::new();
    let mut model = Vec::new();
    let mut state = 0x5A5A_4321_u32;

    for _ in 0..10_000 {
        state = state.wrapping_mul(1_664_525).wrapping_add(1_013_904_223);
        match state % 4 {
            0 | 1 => {
                let value = state as i32;
                stack.push(value);
                model.push(value);
            }
            2 => assert_eq!(stack.pop(), model.pop()),
            _ => {
                assert_eq!(stack.peek(), model.last());
                assert_eq!(stack.bottom(), model.first());
            }
        }

        assert_eq!(stack.len(), model.len());
        assert_eq!(
            stack.iter().copied().collect::<Vec<_>>(),
            model.iter().rev().copied().collect::<Vec<_>>()
        );
    }
}
