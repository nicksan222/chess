//! General-purpose collections with project-relevant semantics.

mod linked_list;
mod queue;

pub use linked_list::{IntoIter, Iter, IterMut, LinkedList};
pub use queue::{IntoIter as QueueIntoIter, Iter as QueueIter, IterMut as QueueIterMut, Queue};
