use core::{
    iter::{FusedIterator, Rev},
    slice,
};

use super::CapacityError;

/// A fixed-capacity, allocator-free last-in, first-out stack.
///
/// Push, pop, and peek operations are `O(1)`. The stack stores its `N` slots
/// inline and returns rejected elements when full.
pub struct ArrayStack<T, const N: usize> {
    slots: [Option<T>; N],
    len: usize,
}

impl<T, const N: usize> ArrayStack<T, N> {
    /// The maximum number of elements this stack can hold.
    pub const CAPACITY: usize = N;

    /// Creates an empty stack.
    #[must_use]
    pub fn new() -> Self {
        Self {
            slots: core::array::from_fn(|_| None),
            len: 0,
        }
    }

    /// Creates a full stack by pushing array elements from left to right.
    ///
    /// The final array element becomes the top.
    #[must_use]
    pub fn from_array(elements: [T; N]) -> Self {
        Self {
            slots: elements.map(Some),
            len: N,
        }
    }

    /// Creates a full stack containing `N` clones of `element`.
    #[must_use]
    pub fn from_repeated(element: T) -> Self
    where
        T: Clone,
    {
        Self::from_array(core::array::from_fn(|_| element.clone()))
    }

    /// Returns the number of elements currently stored.
    #[must_use]
    pub const fn len(&self) -> usize {
        self.len
    }

    /// Returns `true` when the stack contains no elements.
    #[must_use]
    pub const fn is_empty(&self) -> bool {
        self.len == 0
    }

    /// Returns `true` when no additional element can be pushed.
    ///
    /// A zero-capacity stack is both empty and full.
    #[must_use]
    pub const fn is_full(&self) -> bool {
        self.len == N
    }

    /// Returns the fixed capacity of the stack.
    #[must_use]
    pub const fn capacity(&self) -> usize {
        N
    }

    /// Attempts to push `element` onto the top.
    ///
    /// If the stack is full, it remains unchanged and the error owns the
    /// rejected element.
    ///
    /// # Errors
    ///
    /// Returns [`CapacityError`] carrying `element` when the stack is full.
    pub fn try_push(&mut self, element: T) -> Result<(), CapacityError<T>> {
        if self.is_full() {
            return Err(CapacityError::new(element));
        }

        self.slots[self.len] = Some(element);
        self.len += 1;
        Ok(())
    }

    /// Removes and returns the top element.
    #[must_use]
    pub fn pop(&mut self) -> Option<T> {
        if self.is_empty() {
            return None;
        }

        self.len -= 1;
        self.slots[self.len].take()
    }

    /// Returns a shared reference to the top element.
    #[must_use]
    pub fn peek(&self) -> Option<&T> {
        if self.is_empty() {
            None
        } else {
            self.slots[self.len - 1].as_ref()
        }
    }

    /// Returns an exclusive reference to the top element.
    #[must_use]
    pub fn peek_mut(&mut self) -> Option<&mut T> {
        if self.is_empty() {
            None
        } else {
            self.slots[self.len - 1].as_mut()
        }
    }

    /// Returns a shared reference to the bottom element.
    #[must_use]
    pub fn bottom(&self) -> Option<&T> {
        self.slots.first().and_then(Option::as_ref)
    }

    /// Returns an exclusive reference to the bottom element.
    #[must_use]
    pub fn bottom_mut(&mut self) -> Option<&mut T> {
        self.slots.first_mut().and_then(Option::as_mut)
    }

    /// Removes elements from the top until at most `len` remain.
    pub fn truncate(&mut self, len: usize) {
        while self.len > len {
            let _ = self.pop();
        }
    }

    /// Removes all elements.
    pub fn clear(&mut self) {
        self.truncate(0);
    }

    /// Returns an iterator from top to bottom in pop order.
    pub fn iter(&self) -> Iter<'_, T> {
        Iter {
            slots: self.slots[..self.len].iter().rev(),
        }
    }

    /// Returns an exclusive iterator from top to bottom in pop order.
    pub fn iter_mut(&mut self) -> IterMut<'_, T> {
        IterMut {
            slots: self.slots[..self.len].iter_mut().rev(),
        }
    }
}

impl_sequence_traits! {
    impl[T, const N: usize] ArrayStack<T, N> {
        iter: Iter<'a, T>,
        iter_mut: IterMut<'a, T>,
    }
}

impl_iteration_order_traits!(impl[T, const N: usize] ArrayStack<T, N>);

impl<T: Clone, const N: usize> Clone for ArrayStack<T, N> {
    fn clone(&self) -> Self {
        let mut clone = Self::new();
        for (destination, source) in clone.slots.iter_mut().zip(&self.slots) {
            destination.clone_from(source);
        }
        clone.len = self.len;
        clone
    }
}

impl<T, const N: usize> From<[T; N]> for ArrayStack<T, N> {
    fn from(elements: [T; N]) -> Self {
        Self::from_array(elements)
    }
}

impl<T, const N: usize> IntoIterator for ArrayStack<T, N> {
    type Item = T;
    type IntoIter = IntoIter<T, N>;

    fn into_iter(self) -> Self::IntoIter {
        IntoIter { stack: self }
    }
}

/// A consuming iterator over an [`ArrayStack`] in pop order.
#[derive(Debug)]
pub struct IntoIter<T, const N: usize> {
    stack: ArrayStack<T, N>,
}

impl<T, const N: usize> Iterator for IntoIter<T, N> {
    type Item = T;

    fn next(&mut self) -> Option<Self::Item> {
        self.stack.pop()
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        (self.stack.len, Some(self.stack.len))
    }
}

impl<T, const N: usize> ExactSizeIterator for IntoIter<T, N> {}
impl<T, const N: usize> FusedIterator for IntoIter<T, N> {}

/// An iterator over shared stack elements in pop order.
#[derive(Debug)]
pub struct Iter<'a, T> {
    slots: Rev<slice::Iter<'a, Option<T>>>,
}

impl<'a, T> Iterator for Iter<'a, T> {
    type Item = &'a T;

    fn next(&mut self) -> Option<Self::Item> {
        // Occupied slots always hold an element, so `and_then` never drops one.
        self.slots.next().and_then(Option::as_ref)
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        self.slots.size_hint()
    }
}

impl<T> ExactSizeIterator for Iter<'_, T> {}
impl<T> FusedIterator for Iter<'_, T> {}

/// An iterator over exclusive stack elements in pop order.
#[derive(Debug)]
pub struct IterMut<'a, T> {
    slots: Rev<slice::IterMut<'a, Option<T>>>,
}

impl<'a, T> Iterator for IterMut<'a, T> {
    type Item = &'a mut T;

    fn next(&mut self) -> Option<Self::Item> {
        // Occupied slots always hold an element, so `and_then` never drops one.
        self.slots.next().and_then(Option::as_mut)
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        self.slots.size_hint()
    }
}

impl<T> ExactSizeIterator for IterMut<'_, T> {}
impl<T> FusedIterator for IterMut<'_, T> {}
