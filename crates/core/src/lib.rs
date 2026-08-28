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
