//! General-purpose collections with project-relevant semantics.

mod linked_list;
mod queue;
mod stack;

pub use linked_list::{IntoIter, Iter, IterMut, LinkedList};
pub use queue::{IntoIter as QueueIntoIter, Iter as QueueIter, IterMut as QueueIterMut, Queue};
pub use stack::{IntoIter as StackIntoIter, Iter as StackIter, IterMut as StackIterMut, Stack};
