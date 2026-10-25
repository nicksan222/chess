use core::{iter::FusedIterator, slice};

use super::CapacityError;

/// A fixed-capacity, allocator-free first-in, first-out ring buffer.
///
/// Push, pop, and indexed position calculations are `O(1)`. The buffer never
/// allocates and stores its `N` slots inline. [`RingBuffer::try_push`] preserves
/// existing data when full, while [`RingBuffer::push_overwrite`] explicitly
/// replaces the oldest element.
pub struct RingBuffer<T, const N: usize> {
    slots: [Option<T>; N],
    head: usize,
    len: usize,
}

impl<T, const N: usize> RingBuffer<T, N> {
    /// The maximum number of elements this buffer can hold.
    pub const CAPACITY: usize = N;

    /// Creates an empty buffer.
    #[must_use]
    pub fn new() -> Self {
        Self {
            slots: core::array::from_fn(|_| None),
            head: 0,
            len: 0,
        }
    }

    /// Creates a full buffer whose elements are popped in array order.
    #[must_use]
    pub fn from_array(elements: [T; N]) -> Self {
        Self {
            slots: elements.map(Some),
            head: 0,
            len: N,
        }
    }

    /// Creates a full buffer containing `N` clones of `element`.
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

    /// Returns `true` when the buffer contains no elements.
    #[must_use]
    pub const fn is_empty(&self) -> bool {
        self.len == 0
    }

    /// Returns `true` when no additional element can be inserted.
    ///
    /// A zero-capacity buffer is both empty and full.
    #[must_use]
    pub const fn is_full(&self) -> bool {
        self.len == N
    }

    /// Returns the fixed capacity of the buffer.
    #[must_use]
    pub const fn capacity(&self) -> usize {
        N
    }

    /// Attempts to add `element` to the back of the buffer.
    ///
    /// If the buffer is full, the buffer remains unchanged and the error owns
    /// the rejected element.
    ///
    /// # Errors
    ///
    /// Returns [`CapacityError`] carrying `element` when the buffer is full.
    pub fn try_push(&mut self, element: T) -> Result<(), CapacityError<T>> {
        if self.is_full() {
            return Err(CapacityError::new(element));
        }

        self.push_unchecked(element);
        Ok(())
    }

    /// Adds `element`, replacing and returning the oldest element when full.
    ///
    /// For a zero-capacity buffer, the incoming element is returned unchanged.
    pub fn push_overwrite(&mut self, element: T) -> Option<T> {
        if N == 0 {
            return Some(element);
        }

        if self.is_full() {
            let displaced = self.slots[self.head].replace(element);
            self.head = Self::next_index(self.head);
            return displaced;
        }

        self.push_unchecked(element);
        None
    }

    /// Removes and returns the oldest element.
    #[must_use]
    pub fn pop(&mut self) -> Option<T> {
        if self.is_empty() {
            return None;
        }

        let element = self.slots[self.head].take();
        self.head = Self::next_index(self.head);
        self.len -= 1;
        if self.len == 0 {
            self.head = 0;
        }
        element
    }

    /// Returns a shared reference to the oldest element.
    #[must_use]
    pub fn front(&self) -> Option<&T> {
        let index = self.slot_index(0)?;
        self.slots[index].as_ref()
    }

    /// Returns an exclusive reference to the oldest element.
    #[must_use]
    pub fn front_mut(&mut self) -> Option<&mut T> {
        let index = self.slot_index(0)?;
        self.slots[index].as_mut()
    }

    /// Returns a shared reference to the newest element.
    #[must_use]
    pub fn back(&self) -> Option<&T> {
        let index = self.slot_index(self.len.checked_sub(1)?)?;
        self.slots[index].as_ref()
    }

    /// Returns an exclusive reference to the newest element.
    #[must_use]
    pub fn back_mut(&mut self) -> Option<&mut T> {
        let index = self.slot_index(self.len.checked_sub(1)?)?;
        self.slots[index].as_mut()
    }

    /// Removes all elements.
    pub fn clear(&mut self) {
        while self.pop().is_some() {}
    }

    /// Returns an iterator from oldest to newest.
    pub fn iter(&self) -> Iter<'_, T, N> {
        Iter {
            buffer: self,
            offset: 0,
        }
    }

    /// Returns an exclusive iterator from oldest to newest.
    pub fn iter_mut(&mut self) -> IterMut<'_, T> {
        let first_len = self.len.min(N.saturating_sub(self.head));
        let second_len = self.len - first_len;
        let (before_head, from_head) = self.slots.split_at_mut(self.head);

        IterMut {
            first: from_head[..first_len].iter_mut(),
            second: before_head[..second_len].iter_mut(),
            remaining: self.len,
        }
    }

    /// Returns the slot holding the element `offset` places after the oldest,
    /// or `None` when `offset` is not an occupied position.
    fn slot_index(&self, offset: usize) -> Option<usize> {
        (offset < self.len).then(|| self.logical_index(offset))
    }

    /// Stores `element` after the newest one. The caller must ensure the
    /// buffer is not full.
    fn push_unchecked(&mut self, element: T) {
        debug_assert!(!self.is_full());
        let index = self.logical_index(self.len);
        self.slots[index] = Some(element);
        self.len += 1;
    }

    fn logical_index(&self, offset: usize) -> usize {
        debug_assert!(N > 0);
        debug_assert!(offset < N);
        let until_end = N - self.head;
        if offset < until_end {
            self.head + offset
        } else {
            offset - until_end
        }
    }

    fn next_index(index: usize) -> usize {
        debug_assert!(N > 0);
        if index + 1 == N { 0 } else { index + 1 }
    }
}

impl_sequence_traits! {
    impl[T, const N: usize] RingBuffer<T, N> {
        iter: Iter<'a, T, N>,
        iter_mut: IterMut<'a, T>,
    }
}

impl_iteration_order_traits!(impl[T, const N: usize] RingBuffer<T, N>);

impl<T: Clone, const N: usize> Clone for RingBuffer<T, N> {
    fn clone(&self) -> Self {
        let mut clone = Self::new();
        for element in self {
            clone.push_unchecked(element.clone());
        }
        clone
    }
}

impl<T, const N: usize> From<[T; N]> for RingBuffer<T, N> {
    fn from(elements: [T; N]) -> Self {
        Self::from_array(elements)
    }
}

impl<T, const N: usize> IntoIterator for RingBuffer<T, N> {
    type Item = T;
    type IntoIter = IntoIter<T, N>;

    fn into_iter(self) -> Self::IntoIter {
        IntoIter { buffer: self }
    }
}

/// A consuming iterator over a [`RingBuffer`] from oldest to newest.
#[derive(Debug)]
pub struct IntoIter<T, const N: usize> {
    buffer: RingBuffer<T, N>,
}

impl<T, const N: usize> Iterator for IntoIter<T, N> {
    type Item = T;

    fn next(&mut self) -> Option<Self::Item> {
        self.buffer.pop()
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        (self.buffer.len, Some(self.buffer.len))
    }
}

impl<T, const N: usize> ExactSizeIterator for IntoIter<T, N> {}
impl<T, const N: usize> FusedIterator for IntoIter<T, N> {}

/// An iterator over shared ring-buffer elements from oldest to newest.
#[derive(Debug)]
pub struct Iter<'a, T, const N: usize> {
    buffer: &'a RingBuffer<T, N>,
    offset: usize,
}

impl<'a, T, const N: usize> Iterator for Iter<'a, T, N> {
    type Item = &'a T;

    fn next(&mut self) -> Option<Self::Item> {
        if self.offset == self.buffer.len {
            return None;
        }

        let index = self.buffer.logical_index(self.offset);
        self.offset += 1;
        self.buffer.slots[index].as_ref()
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        let remaining = self.buffer.len - self.offset;
        (remaining, Some(remaining))
    }
}

impl<T, const N: usize> ExactSizeIterator for Iter<'_, T, N> {}
impl<T, const N: usize> FusedIterator for Iter<'_, T, N> {}

/// An iterator over exclusive ring-buffer elements from oldest to newest.
#[derive(Debug)]
pub struct IterMut<'a, T> {
    first: slice::IterMut<'a, Option<T>>,
    second: slice::IterMut<'a, Option<T>>,
    remaining: usize,
}

impl<'a, T> Iterator for IterMut<'a, T> {
    type Item = &'a mut T;

    fn next(&mut self) -> Option<Self::Item> {
        let slot = self.first.next().or_else(|| self.second.next())?;
        // Occupied ranges always hold an element.
        let element = slot.as_mut()?;
        self.remaining -= 1;
        Some(element)
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        (self.remaining, Some(self.remaining))
    }
}

impl<T> ExactSizeIterator for IterMut<'_, T> {}
impl<T> FusedIterator for IterMut<'_, T> {}
