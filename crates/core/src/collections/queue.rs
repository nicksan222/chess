use alloc::collections::{TryReserveError, VecDeque, vec_deque};
use core::{fmt, hash::Hash};

/// An allocator-backed first-in, first-out queue.
///
/// Enqueueing and dequeueing are amortized `O(1)`. The queue may wrap its
/// storage internally, but iteration always follows dequeue order from the
/// oldest element to the newest.
#[derive(Clone, PartialEq, Eq, PartialOrd, Ord, Hash)]
pub struct Queue<T> {
    elements: VecDeque<T>,
}

impl<T> Queue<T> {
    /// Creates an empty queue without allocating.
    #[must_use]
    pub const fn new() -> Self {
        Self {
            elements: VecDeque::new(),
        }
    }

    /// Creates an empty queue with space for at least `capacity` elements.
    #[must_use]
    pub fn with_capacity(capacity: usize) -> Self {
        Self {
            elements: VecDeque::with_capacity(capacity),
        }
    }

    /// Creates a queue from an array in first-to-last dequeue order.
    #[must_use]
    pub fn from_array<const N: usize>(elements: [T; N]) -> Self {
        elements.into_iter().collect()
    }

    /// Creates a queue containing `count` clones of `element`.
    #[must_use]
    pub fn from_repeated(element: T, count: usize) -> Self
    where
        T: Clone,
    {
        core::iter::repeat_n(element, count).collect()
    }

    /// Returns the number of elements in the queue.
    #[must_use]
    pub fn len(&self) -> usize {
        self.elements.len()
    }

    /// Returns `true` when the queue contains no elements.
    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.elements.is_empty()
    }

    /// Returns the number of elements the queue can hold without reallocating.
    #[must_use]
    pub fn capacity(&self) -> usize {
        self.elements.capacity()
    }

    /// Reserves capacity for at least `additional` more elements.
    ///
    /// # Panics
    ///
    /// Panics if the resulting capacity exceeds `isize::MAX` bytes or if the
    /// allocator reports an error.
    pub fn reserve(&mut self, additional: usize) {
        self.elements.reserve(additional);
    }

    /// Attempts to reserve capacity for at least `additional` more elements.
    ///
    /// The queue remains unchanged when reservation fails.
    pub fn try_reserve(&mut self, additional: usize) -> Result<(), TryReserveError> {
        self.elements.try_reserve(additional)
    }

    /// Shrinks capacity as much as the allocator permits.
    pub fn shrink_to_fit(&mut self) {
        self.elements.shrink_to_fit();
    }

    /// Adds an element to the back of the queue in amortized `O(1)` time.
    pub fn enqueue(&mut self, element: T) {
        self.elements.push_back(element);
    }

    /// Removes and returns the oldest element in amortized `O(1)` time.
    #[must_use]
    pub fn dequeue(&mut self) -> Option<T> {
        self.elements.pop_front()
    }

    /// Returns a shared reference to the element that will be dequeued next.
    #[must_use]
    pub fn peek(&self) -> Option<&T> {
        self.elements.front()
    }

    /// Returns an exclusive reference to the element that will be dequeued next.
    #[must_use]
    pub fn peek_mut(&mut self) -> Option<&mut T> {
        self.elements.front_mut()
    }

    /// Returns a shared reference to the most recently enqueued element.
    #[must_use]
    pub fn back(&self) -> Option<&T> {
        self.elements.back()
    }

    /// Returns an exclusive reference to the most recently enqueued element.
    #[must_use]
    pub fn back_mut(&mut self) -> Option<&mut T> {
        self.elements.back_mut()
    }

    /// Moves every element from `other` to the back of this queue.
    ///
    /// Elements retain their dequeue order, and `other` is empty afterward.
    pub fn append(&mut self, other: &mut Self) {
        self.elements.append(&mut other.elements);
    }

    /// Removes every element while retaining allocated storage for reuse.
    pub fn clear(&mut self) {
        self.elements.clear();
    }

    /// Retains only elements for which `predicate` returns `true`.
    ///
    /// Elements are visited exactly once in dequeue order.
    pub fn retain<F>(&mut self, predicate: F)
    where
        F: FnMut(&T) -> bool,
    {
        self.elements.retain(predicate);
    }

    /// Returns an iterator in dequeue order.
    pub fn iter(&self) -> Iter<'_, T> {
        self.elements.iter()
    }

    /// Returns an exclusive iterator in dequeue order.
    pub fn iter_mut(&mut self) -> IterMut<'_, T> {
        self.elements.iter_mut()
    }
}

impl<T> Default for Queue<T> {
    fn default() -> Self {
        Self::new()
    }
}

impl<T: fmt::Debug> fmt::Debug for Queue<T> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.debug_list().entries(self).finish()
    }
}

impl<T> Extend<T> for Queue<T> {
    fn extend<I: IntoIterator<Item = T>>(&mut self, iter: I) {
        self.elements.extend(iter);
    }
}

impl<'a, T: Clone + 'a> Extend<&'a T> for Queue<T> {
    fn extend<I: IntoIterator<Item = &'a T>>(&mut self, iter: I) {
        self.elements.extend(iter.into_iter().cloned());
    }
}

impl<T> FromIterator<T> for Queue<T> {
    fn from_iter<I: IntoIterator<Item = T>>(iter: I) -> Self {
        Self {
            elements: iter.into_iter().collect(),
        }
    }
}

impl<T, const N: usize> From<[T; N]> for Queue<T> {
    fn from(elements: [T; N]) -> Self {
        Self::from_array(elements)
    }
}

impl<T> From<VecDeque<T>> for Queue<T> {
    fn from(elements: VecDeque<T>) -> Self {
        Self { elements }
    }
}

impl<T> From<Queue<T>> for VecDeque<T> {
    fn from(queue: Queue<T>) -> Self {
        queue.elements
    }
}

impl<T> IntoIterator for Queue<T> {
    type Item = T;
    type IntoIter = IntoIter<T>;

    fn into_iter(self) -> Self::IntoIter {
        self.elements.into_iter()
    }
}

impl<'a, T> IntoIterator for &'a Queue<T> {
    type Item = &'a T;
    type IntoIter = Iter<'a, T>;

    fn into_iter(self) -> Self::IntoIter {
        self.iter()
    }
}

impl<'a, T> IntoIterator for &'a mut Queue<T> {
    type Item = &'a mut T;
    type IntoIter = IterMut<'a, T>;

    fn into_iter(self) -> Self::IntoIter {
        self.iter_mut()
    }
}

/// A consuming iterator over a [`Queue`] in dequeue order.
pub type IntoIter<T> = vec_deque::IntoIter<T>;

/// An iterator over shared queue elements in dequeue order.
pub type Iter<'a, T> = vec_deque::Iter<'a, T>;

/// An iterator over exclusive queue elements in dequeue order.
pub type IterMut<'a, T> = vec_deque::IterMut<'a, T>;
