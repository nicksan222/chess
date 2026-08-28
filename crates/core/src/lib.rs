//! Small, integration-neutral building blocks shared across the project.
//!
//! This crate deliberately avoids becoming a general-purpose utility crate.
//! Every exported building block should have a concrete project-level use case.

#![no_std]
#![forbid(unsafe_code)]

extern crate alloc;

pub mod collections;

/// Creates an owned [`LinkedList`](crate::collections::LinkedList).
///
/// Elements are evaluated once, from left to right, and retain that order in
/// the resulting list.
///
/// # Examples
///
/// ```
/// use chess_core::{collections::LinkedList, linked_list};
///
/// let empty: LinkedList<i32> = linked_list![];
/// let values = linked_list![1, 2, 3];
/// let repeated = linked_list!["square"; 3];
///
/// assert!(empty.is_empty());
/// assert_eq!(values.iter().copied().collect::<Vec<_>>(), [1, 2, 3]);
/// assert_eq!(repeated.len(), 3);
/// ```
#[macro_export]
macro_rules! linked_list {
    () => {
        $crate::collections::LinkedList::new()
    };
    ($element:expr; $count:expr) => {{
        $crate::collections::LinkedList::from_repeated($element, $count)
    }};
    ($($element:expr),+ $(,)?) => {{
        $crate::collections::LinkedList::from_array([$($element),+])
    }};
}

/// Creates a first-in, first-out [`Queue`](crate::collections::Queue).
///
/// Elements are evaluated once, from left to right. The leftmost element is
/// dequeued first.
///
/// # Examples
///
/// ```
/// use chess_core::{collections::Queue, queue};
///
/// let empty: Queue<i32> = queue![];
/// let mut turns = queue!["white", "black"];
/// let repeated = queue![0; 3];
///
/// assert!(empty.is_empty());
/// assert_eq!(turns.dequeue(), Some("white"));
/// assert_eq!(repeated.len(), 3);
/// ```
#[macro_export]
macro_rules! queue {
    () => {
        $crate::collections::Queue::new()
    };
    ($element:expr; $count:expr) => {{
        $crate::collections::Queue::from_repeated($element, $count)
    }};
    ($($element:expr),+ $(,)?) => {{
        $crate::collections::Queue::from_array([$($element),+])
    }};
}

/// Creates a last-in, first-out [`Stack`](crate::collections::Stack).
///
/// Elements are evaluated and pushed once, from left to right. The rightmost
/// element becomes the top and is popped first.
///
/// # Examples
///
/// ```
/// use chess_core::{collections::Stack, stack};
///
/// let empty: Stack<i32> = stack![];
/// let mut moves = stack!["e2e4", "e7e5"];
/// let repeated = stack![0; 3];
///
/// assert!(empty.is_empty());
/// assert_eq!(moves.pop(), Some("e7e5"));
/// assert_eq!(repeated.len(), 3);
/// ```
#[macro_export]
macro_rules! stack {
    () => {
        $crate::collections::Stack::new()
    };
    ($element:expr; $count:expr) => {{
        $crate::collections::Stack::from_repeated($element, $count)
    }};
    ($($element:expr),+ $(,)?) => {{
        $crate::collections::Stack::from_array([$($element),+])
    }};
}
