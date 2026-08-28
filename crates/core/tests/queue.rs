use std::{cell::Cell, collections::VecDeque};

use chess_core::{collections::Queue, queue};

fn values<T: Copy>(queue: &Queue<T>) -> Vec<T> {
    queue.iter().copied().collect()
}

#[test]
fn new_queue_is_empty_without_capacity() {
    let queue = Queue::<i32>::new();

    assert!(queue.is_empty());
    assert_eq!(queue.len(), 0);
    assert_eq!(queue.capacity(), 0);
    assert_eq!(queue.peek(), None);
    assert_eq!(queue.back(), None);
}

#[test]
fn enqueue_and_dequeue_follow_fifo_order() {
    let mut queue = Queue::new();

    queue.enqueue(1);
    queue.enqueue(2);
    queue.enqueue(3);

    assert_eq!(queue.len(), 3);
    assert_eq!(queue.peek(), Some(&1));
    assert_eq!(queue.back(), Some(&3));
    assert_eq!(queue.dequeue(), Some(1));
    assert_eq!(queue.dequeue(), Some(2));
    assert_eq!(queue.dequeue(), Some(3));
    assert_eq!(queue.dequeue(), None);
    assert!(queue.is_empty());
}

#[test]
fn mutable_access_does_not_change_queue_order() {
    let mut queue = queue![1, 2, 3];

    *queue.peek_mut().expect("front exists") = 10;
    *queue.back_mut().expect("back exists") = 30;
    for value in &mut queue {
        *value += 1;
    }

    assert_eq!(values(&queue), [11, 3, 31]);
}

#[test]
fn append_preserves_each_queues_order_and_empties_source() {
    let mut first = queue![1, 2];
    let mut second = queue![3, 4];

    first.append(&mut second);

    assert_eq!(values(&first), [1, 2, 3, 4]);
    assert!(second.is_empty());
}

#[test]
fn retain_visits_and_preserves_dequeue_order() {
    let mut queue = queue![1, 2, 3, 4, 5, 6];
    let mut visited = Vec::new();

    queue.retain(|value| {
        visited.push(*value);
        value % 2 == 0
    });

    assert_eq!(visited, [1, 2, 3, 4, 5, 6]);
    assert_eq!(values(&queue), [2, 4, 6]);
}

#[test]
fn capacity_can_be_managed_without_changing_elements() {
    let mut queue = Queue::with_capacity(2);
    queue.extend([1, 2]);
    let old_capacity = queue.capacity();

    queue.reserve(10);
    assert!(queue.capacity() >= queue.len() + 10);
    assert!(queue.capacity() >= old_capacity);
    assert_eq!(values(&queue), [1, 2]);

    queue.shrink_to_fit();
    assert!(queue.capacity() >= queue.len());
    assert_eq!(values(&queue), [1, 2]);
}

#[test]
fn failed_reservation_leaves_queue_unchanged() {
    let mut queue = queue![1, 2, 3];
    let capacity = queue.capacity();

    assert!(queue.try_reserve(usize::MAX).is_err());
    assert_eq!(queue.capacity(), capacity);
    assert_eq!(values(&queue), [1, 2, 3]);
}

#[test]
fn construction_conversion_and_extension_preserve_order() {
    let mut queue = Queue::from([1, 2]);
    queue.extend([3, 4]);
    queue.extend(&[5, 6]);

    let deque: VecDeque<_> = queue.clone().into();
    let round_trip = Queue::from(deque);

    assert_eq!(values(&queue), [1, 2, 3, 4, 5, 6]);
    assert_eq!(round_trip, queue);
    assert_eq!(
        queue.clone().into_iter().collect::<Vec<_>>(),
        [1, 2, 3, 4, 5, 6]
    );
    assert_eq!(format!("{queue:?}"), "[1, 2, 3, 4, 5, 6]");
}

#[test]
fn clear_reuses_queue_without_observable_stale_elements() {
    let mut queue = Queue::with_capacity(8);
    queue.extend(0..8);
    let capacity = queue.capacity();

    queue.clear();
    assert!(queue.is_empty());
    assert_eq!(queue.capacity(), capacity);

    queue.extend([10, 11]);
    assert_eq!(values(&queue), [10, 11]);
}

#[test]
fn macro_supports_all_forms_and_evaluates_in_fifo_order() {
    let empty: Queue<u8> = queue![];
    let order = Cell::new(0);
    let next = || {
        let value = order.get();
        order.set(value + 1);
        value
    };

    let elements = queue![next(), next(), next(),];
    let repeated = queue![String::from("event"); 3];

    assert!(empty.is_empty());
    assert_eq!(values(&elements), [0, 1, 2]);
    assert_eq!(order.get(), 3);
    assert_eq!(
        repeated.into_iter().collect::<Vec<_>>(),
        ["event", "event", "event"]
    );
}

#[test]
fn operation_sequence_matches_vec_deque_model() {
    let mut queue = Queue::new();
    let mut model = VecDeque::new();
    let mut state = 0xA5A5_1234_u32;

    for _ in 0..10_000 {
        state = state.wrapping_mul(1_664_525).wrapping_add(1_013_904_223);
        match state % 4 {
            0 | 1 => {
                let value = state as i32;
                queue.enqueue(value);
                model.push_back(value);
            }
            2 => assert_eq!(queue.dequeue(), model.pop_front()),
            _ => {
                assert_eq!(queue.peek(), model.front());
                assert_eq!(queue.back(), model.back());
            }
        }

        assert_eq!(queue.len(), model.len());
        assert_eq!(
            queue.iter().copied().collect::<Vec<_>>(),
            model.iter().copied().collect::<Vec<_>>()
        );
    }
}
