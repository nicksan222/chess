use alloc::{
    collections::TryReserveError,
    vec::{self, Vec},
};
use core::{iter::Rev, slice};

/// An allocator-backed last-in, first-out stack.
///
/// Pushing and popping are amortized `O(1)`. All iterators follow pop order,
/// from the top of the stack to the bottom.
#[derive(Clone)]
pub struct Stack<T> {
    elements: Vec<T>,
}

impl<T> Stack<T> {
    /// Creates an empty stack without allocating.
    #[must_use]
    pub const fn new() -> Self {
        Self {
            elements: Vec::new(),
        }
    }

    /// Creates an empty stack with space for at least `capacity` elements.
    #[must_use]
    pub fn with_capacity(capacity: usize) -> Self {
        Self {
            elements: Vec::with_capacity(capacity),
        }
    }

    /// Creates a stack by pushing array elements from left to right.
    ///
    /// The final array element becomes the top of the stack.
    #[must_use]
    pub fn from_array<const N: usize>(elements: [T; N]) -> Self {
        Self {
            elements: Vec::from(elements),
        }
    }

    /// Creates a stack containing `count` clones of `element`.
    #[must_use]
    pub fn from_repeated(element: T, count: usize) -> Self
    where
        T: Clone,
    {
        Self {
            elements: alloc::vec![element; count],
        }
    }

    /// Returns the number of elements in the stack.
    #[must_use]
    pub fn len(&self) -> usize {
        self.elements.len()
    }

    /// Returns `true` when the stack contains no elements.
    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.elements.is_empty()
    }

    /// Returns the number of elements the stack can hold without reallocating.
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
    /// The stack remains unchanged when reservation fails.
    ///
    /// # Errors
    ///
    /// Returns [`TryReserveError`] when the capacity overflows or the allocator
    /// reports a failure.
    pub fn try_reserve(&mut self, additional: usize) -> Result<(), TryReserveError> {
        self.elements.try_reserve(additional)
    }

    /// Shrinks capacity as much as the allocator permits.
    pub fn shrink_to_fit(&mut self) {
        self.elements.shrink_to_fit();
    }

    /// Pushes an element onto the top in amortized `O(1)` time.
    pub fn push(&mut self, element: T) {
        self.elements.push(element);
    }

    /// Removes and returns the top element in amortized `O(1)` time.
    #[must_use]
    pub fn pop(&mut self) -> Option<T> {
        self.elements.pop()
    }

    /// Returns a shared reference to the top element.
    #[must_use]
    pub fn peek(&self) -> Option<&T> {
        self.elements.last()
    }

    /// Returns an exclusive reference to the top element.
    #[must_use]
    pub fn peek_mut(&mut self) -> Option<&mut T> {
        self.elements.last_mut()
    }

    /// Returns a shared reference to the bottom element.
    #[must_use]
    pub fn bottom(&self) -> Option<&T> {
        self.elements.first()
    }

    /// Returns an exclusive reference to the bottom element.
    #[must_use]
    pub fn bottom_mut(&mut self) -> Option<&mut T> {
        self.elements.first_mut()
    }

    /// Moves `other` onto the top of this stack.
    ///
    /// `other` is empty afterward. Its top remains the first element popped
    /// from the combined stack.
    pub fn append(&mut self, other: &mut Self) {
        self.elements.append(&mut other.elements);
    }

    /// Removes elements from the top until at most `len` remain.
    pub fn truncate(&mut self, len: usize) {
        self.elements.truncate(len);
    }

    /// Removes every element while retaining allocated storage for reuse.
    pub fn clear(&mut self) {
        self.elements.clear();
    }

    /// Returns an iterator from top to bottom in pop order.
    pub fn iter(&self) -> Iter<'_, T> {
        self.elements.iter().rev()
    }

    /// Returns an exclusive iterator from top to bottom in pop order.
    pub fn iter_mut(&mut self) -> IterMut<'_, T> {
        self.elements.iter_mut().rev()
    }
}

impl_sequence_traits! {
    impl[T] Stack<T> {
        iter: Iter<'a, T>,
        iter_mut: IterMut<'a, T>,
    }
}

impl_iteration_order_traits!(impl[T] Stack<T>);

impl<T> Extend<T> for Stack<T> {
    fn extend<I: IntoIterator<Item = T>>(&mut self, iter: I) {
        self.elements.extend(iter);
    }
}

impl<'a, T: Clone + 'a> Extend<&'a T> for Stack<T> {
    fn extend<I: IntoIterator<Item = &'a T>>(&mut self, iter: I) {
        self.elements.extend(iter.into_iter().cloned());
    }
}

impl<T> FromIterator<T> for Stack<T> {
    fn from_iter<I: IntoIterator<Item = T>>(iter: I) -> Self {
        Self {
            elements: iter.into_iter().collect(),
        }
    }
}

impl<T, const N: usize> From<[T; N]> for Stack<T> {
    fn from(elements: [T; N]) -> Self {
        Self::from_array(elements)
    }
}

impl<T> From<Vec<T>> for Stack<T> {
    fn from(elements: Vec<T>) -> Self {
        Self { elements }
    }
}

impl<T> From<Stack<T>> for Vec<T> {
    fn from(stack: Stack<T>) -> Self {
        stack.elements
    }
}

impl<T> IntoIterator for Stack<T> {
    type Item = T;
    type IntoIter = IntoIter<T>;

    fn into_iter(self) -> Self::IntoIter {
        self.elements.into_iter().rev()
    }
}

/// A consuming iterator over a [`Stack`] in pop order.
pub type IntoIter<T> = Rev<vec::IntoIter<T>>;

/// An iterator over shared stack elements in pop order.
pub type Iter<'a, T> = Rev<slice::Iter<'a, T>>;

/// An iterator over exclusive stack elements in pop order.
pub type IterMut<'a, T> = Rev<slice::IterMut<'a, T>>;
