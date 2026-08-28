use std::{
    cell::Cell,
    collections::hash_map::DefaultHasher,
    hash::{Hash, Hasher},
    rc::Rc,
};

use chess_core::{collections::LinkedList, linked_list};

fn values<T: Copy>(list: &LinkedList<T>) -> Vec<T> {
    list.iter().copied().collect()
}

#[test]
fn new_list_is_empty() {
    let list = LinkedList::<i32>::new();

    assert!(list.is_empty());
    assert_eq!(list.len(), 0);
    assert_eq!(list.front(), None);
    assert_eq!(list.back(), None);
    assert_eq!(list.iter().size_hint(), (0, Some(0)));
}

#[test]
fn front_operations_update_both_ends_and_length() {
    let mut list = LinkedList::new();

    list.push_front(2);
    list.push_front(1);
    *list.front_mut().expect("front exists") = 0;

    assert_eq!(list.len(), 2);
    assert_eq!(list.front(), Some(&0));
    assert_eq!(list.back(), Some(&2));
    assert_eq!(list.pop_front(), Some(0));
    assert_eq!(list.pop_front(), Some(2));
    assert_eq!(list.pop_front(), None);
    assert!(list.is_empty());
}

#[test]
fn back_operations_preserve_order() {
    let mut list = LinkedList::new();

    list.push_back(1);
    list.push_back(2);
    list.push_back(3);
    *list.back_mut().expect("back exists") = 4;

    assert_eq!(values(&list), [1, 2, 4]);
    assert_eq!(list.pop_back(), Some(4));
    assert_eq!(list.pop_back(), Some(2));
    assert_eq!(list.pop_back(), Some(1));
    assert_eq!(list.pop_back(), None);
    assert!(list.is_empty());
}

#[test]
fn append_moves_nodes_and_empties_source() {
    let mut left = linked_list![1, 2];
    let mut right = linked_list![3, 4];

    left.append(&mut right);

    assert_eq!(values(&left), [1, 2, 3, 4]);
    assert!(right.is_empty());

    let mut empty = LinkedList::new();
    empty.append(&mut left);
    assert_eq!(values(&empty), [1, 2, 3, 4]);
    assert!(left.is_empty());
}

#[test]
fn extend_and_collect_preserve_order() {
    let mut list: LinkedList<_> = [1, 2].into_iter().collect();
    list.extend([3, 4]);
    list.extend(&[5, 6]);

    assert_eq!(values(&list), [1, 2, 3, 4, 5, 6]);
    assert_eq!(LinkedList::from([7, 8]), linked_list![7, 8]);
}

#[test]
fn iterators_are_exact_sized_and_fused() {
    let mut list = linked_list![1, 2, 3];

    let mut iter = list.iter();
    assert_eq!(iter.len(), 3);
    assert_eq!(iter.next(), Some(&1));
    assert_eq!(iter.len(), 2);
    assert_eq!(iter.collect::<Vec<_>>(), [&2, &3]);

    for value in &mut list {
        *value *= 2;
    }
    assert_eq!(values(&list), [2, 4, 6]);

    let mut owned = list.into_iter();
    assert_eq!(owned.len(), 3);
    assert_eq!(owned.by_ref().collect::<Vec<_>>(), [2, 4, 6]);
    assert_eq!(owned.next(), None);
    assert_eq!(owned.next(), None);
}

#[test]
fn macro_supports_empty_elements_trailing_comma_and_repetition() {
    let empty: LinkedList<u8> = linked_list![];
    let elements = linked_list![String::from("a"), String::from("b"),];
    let repeated = linked_list![String::from("x"); 3];

    assert!(empty.is_empty());
    assert_eq!(elements.into_iter().collect::<Vec<_>>(), ["a", "b"]);
    assert_eq!(repeated.into_iter().collect::<Vec<_>>(), ["x", "x", "x"]);
}

#[test]
fn macro_evaluates_elements_once_from_left_to_right() {
    let order = Cell::new(0);
    let next = || {
        let value = order.get();
        order.set(value + 1);
        value
    };

    let list = linked_list![next(), next(), next()];

    assert_eq!(values(&list), [0, 1, 2]);
    assert_eq!(order.get(), 3);
}

#[test]
fn clone_comparison_debug_and_hash_follow_sequence_semantics() {
    let original = linked_list![1, 2, 3];
    let cloned = original.clone();
    let greater = linked_list![1, 2, 4];

    assert_eq!(original, cloned);
    assert!(original < greater);
    assert_eq!(format!("{original:?}"), "[1, 2, 3]");

    let mut original_hash = DefaultHasher::new();
    let mut cloned_hash = DefaultHasher::new();
    original.hash(&mut original_hash);
    cloned.hash(&mut cloned_hash);
    assert_eq!(original_hash.finish(), cloned_hash.finish());
}

#[test]
fn clear_and_drop_release_every_element_exactly_once() {
    struct DropCounter(Rc<Cell<usize>>);

    impl Drop for DropCounter {
        fn drop(&mut self) {
            self.0.set(self.0.get() + 1);
        }
    }

    let drops = Rc::new(Cell::new(0));
    let mut list: LinkedList<_> = (0..10).map(|_| DropCounter(Rc::clone(&drops))).collect();

    list.clear();
    assert_eq!(drops.get(), 10);

    list.extend((0..5).map(|_| DropCounter(Rc::clone(&drops))));
    drop(list);
    assert_eq!(drops.get(), 15);
}

#[test]
fn long_lists_are_destroyed_iteratively() {
    let list: LinkedList<_> = (0..100_000).collect();
    drop(list);
}
