//! General-purpose collections with project-relevant semantics.

mod array_stack;
mod capacity_error;
mod linked_list;
mod queue;
mod ring_buffer;
mod stack;

pub use array_stack::{
    ArrayStack, IntoIter as ArrayStackIntoIter, Iter as ArrayStackIter,
    IterMut as ArrayStackIterMut,
};
pub use capacity_error::CapacityError;
pub use linked_list::{IntoIter, Iter, IterMut, LinkedList};
pub use queue::{IntoIter as QueueIntoIter, Iter as QueueIter, IterMut as QueueIterMut, Queue};
pub use ring_buffer::{
    IntoIter as RingBufferIntoIter, Iter as RingBufferIter, IterMut as RingBufferIterMut,
    RingBuffer,
};
pub use stack::{IntoIter as StackIntoIter, Iter as StackIter, IterMut as StackIterMut, Stack};
