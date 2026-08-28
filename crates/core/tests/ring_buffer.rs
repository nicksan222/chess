use std::{cell::Cell, collections::VecDeque, rc::Rc};

use chess_core::{
    collections::{CapacityError, RingBuffer},
    ring_buffer,
};

fn values<T: Copy, const N: usize>(buffer: &RingBuffer<T, N>) -> Vec<T> {
    buffer.iter().copied().collect()
}

#[test]
fn new_buffer_is_empty_with_fixed_capacity() {
    let buffer = RingBuffer::<i32, 4>::new();

    assert!(buffer.is_empty());
    assert!(!buffer.is_full());
    assert_eq!(buffer.len(), 0);
    assert_eq!(buffer.capacity(), 4);
    assert_eq!(RingBuffer::<i32, 4>::CAPACITY, 4);
    assert_eq!(buffer.front(), None);
    assert_eq!(buffer.back(), None);
}

#[test]
fn zero_capacity_rejects_pushes_and_overwrites_nothing() {
    let mut buffer = RingBuffer::<String, 0>::new();

    let error = buffer
        .try_push(String::from("event"))
        .expect_err("zero-capacity buffer is full");
    assert_eq!(error.element(), "event");
    assert_eq!(error.into_element(), "event");
    assert_eq!(
        buffer.push_overwrite(String::from("new")),
        Some(String::from("new"))
    );
    assert!(buffer.is_empty());
    assert!(buffer.is_full());
    assert_eq!(buffer.pop(), None);
}

#[test]
fn try_push_preserves_fifo_order_and_returns_rejected_element() {
    let mut buffer = RingBuffer::<_, 3>::new();

    buffer.try_push(1).expect("space available");
    buffer.try_push(2).expect("space available");
    buffer.try_push(3).expect("space available");
    let mut error = buffer.try_push(4).expect_err("buffer is full");
    *error.element_mut() = 40;

    assert_eq!(error.into_element(), 40);
    assert_eq!(values(&buffer), [1, 2, 3]);
    assert_eq!(buffer.pop(), Some(1));
    assert_eq!(buffer.pop(), Some(2));
    assert_eq!(buffer.pop(), Some(3));
    assert_eq!(buffer.pop(), None);
}

#[test]
fn overwrite_replaces_only_the_oldest_element() {
    let mut buffer = ring_buffer![1, 2, 3];

    assert_eq!(buffer.push_overwrite(4), Some(1));
    assert_eq!(values(&buffer), [2, 3, 4]);
    assert_eq!(buffer.front(), Some(&2));
    assert_eq!(buffer.back(), Some(&4));
}

#[test]
fn wrapped_mutable_iteration_follows_logical_order() {
    let mut buffer = ring_buffer![1, 2, 3, 4];
    assert_eq!(buffer.pop(), Some(1));
    assert_eq!(buffer.pop(), Some(2));
    buffer.try_push(5).expect("space available");
    buffer.try_push(6).expect("space available");

    let mut visited = Vec::new();
    for element in &mut buffer {
        visited.push(*element);
        *element *= 10;
    }
    *buffer.front_mut().expect("front exists") += 1;
    *buffer.back_mut().expect("back exists") += 1;

    assert_eq!(visited, [3, 4, 5, 6]);
    assert_eq!(values(&buffer), [31, 40, 50, 61]);
}

#[test]
fn macro_supports_all_forms_and_evaluates_left_to_right() {
    let empty: RingBuffer<u8, 0> = ring_buffer![];
    let order = Cell::new(0);
    let next = || {
        let value = order.get();
        order.set(value + 1);
        value
    };

    let elements = ring_buffer![next(), next(), next(),];
    let repeated = ring_buffer![String::from("event"); 3];

    assert!(empty.is_empty());
    assert_eq!(values(&elements), [0, 1, 2]);
    assert_eq!(order.get(), 3);
    assert_eq!(
        repeated.into_iter().collect::<Vec<_>>(),
        ["event", "event", "event"]
    );
}

#[test]
fn clone_comparison_debug_and_consuming_iteration_use_fifo_order() {
    let mut buffer = ring_buffer![1, 2, 3];
    assert_eq!(buffer.pop(), Some(1));
    buffer.try_push(4).expect("space available");
    let clone = buffer.clone();

    assert_eq!(buffer, clone);
    assert!(buffer < ring_buffer![2, 3, 5]);
    assert_eq!(format!("{buffer:?}"), "[2, 3, 4]");
    assert_eq!(clone.into_iter().collect::<Vec<_>>(), [2, 3, 4]);
}

#[test]
fn clear_drops_each_element_once_and_resets_wrapped_state() {
    struct DropCounter(Rc<Cell<usize>>);

    impl Drop for DropCounter {
        fn drop(&mut self) {
            self.0.set(self.0.get() + 1);
        }
    }

    let drops = Rc::new(Cell::new(0));
    let mut buffer = RingBuffer::<_, 4>::new();
    for _ in 0..4 {
        buffer
            .try_push(DropCounter(Rc::clone(&drops)))
            .unwrap_or_else(|_| panic!("space available"));
    }
    drop(buffer.pop());
    buffer
        .try_push(DropCounter(Rc::clone(&drops)))
        .unwrap_or_else(|_| panic!("space available"));

    buffer.clear();
    assert_eq!(drops.get(), 5);
    assert!(buffer.is_empty());

    buffer
        .try_push(DropCounter(Rc::clone(&drops)))
        .unwrap_or_else(|_| panic!("space available"));
    drop(buffer);
    assert_eq!(drops.get(), 6);
}

#[test]
fn operation_sequence_matches_bounded_vec_deque_model() {
    const CAPACITY: usize = 7;
    let mut buffer = RingBuffer::<i32, CAPACITY>::new();
    let mut model = VecDeque::new();
    let mut state = 0x1357_2468_u32;

    for _ in 0..10_000 {
        state = state.wrapping_mul(1_664_525).wrapping_add(1_013_904_223);
        let value = state as i32;
        match state % 4 {
            0 => {
                let actual = buffer.try_push(value).map_err(CapacityError::into_element);
                let expected = if model.len() == CAPACITY {
                    Err(value)
                } else {
                    model.push_back(value);
                    Ok(())
                };
                assert_eq!(actual, expected);
            }
            1 => {
                let expected = if model.len() == CAPACITY {
                    model.pop_front()
                } else {
                    None
                };
                model.push_back(value);
                assert_eq!(buffer.push_overwrite(value), expected);
            }
            2 => assert_eq!(buffer.pop(), model.pop_front()),
            _ => {
                assert_eq!(buffer.front(), model.front());
                assert_eq!(buffer.back(), model.back());
            }
        }

        assert_eq!(buffer.len(), model.len());
        assert_eq!(
            buffer.iter().copied().collect::<Vec<_>>(),
            model.iter().copied().collect::<Vec<_>>()
        );
    }
}
