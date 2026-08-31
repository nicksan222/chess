use alloc::boxed::Box;
use core::{
    cmp::Ordering,
    fmt,
    hash::{Hash, Hasher},
    iter::FusedIterator,
};

/// An owned, singly linked list.
///
/// The implementation uses safe Rust exclusively. Nodes are allocator-backed,
/// so this collection is appropriate for host applications and embedded
/// targets that provide a global allocator. Allocator-free callers should use
/// a fixed-capacity collection instead.
///
/// Insertion and removal at the front are `O(1)`. Operations involving the
/// back are `O(n)` because the list intentionally avoids an unsafe tail pointer.
/// Iteration is `O(n)`.
pub struct LinkedList<T> {
    head: Link<T>,
    len: usize,
}

type Link<T> = Option<Box<Node<T>>>;

struct Node<T> {
    element: T,
    next: Link<T>,
}

impl<T> LinkedList<T> {
    /// Creates an empty list without allocating.
    #[must_use]
    pub const fn new() -> Self {
        Self { head: None, len: 0 }
    }

    /// Creates a list from an array while preserving element order.
    #[must_use]
    pub fn from_array<const N: usize>(elements: [T; N]) -> Self {
        elements.into_iter().collect()
    }

    /// Creates a list containing `count` clones of `element`.
    #[must_use]
    pub fn from_repeated(element: T, count: usize) -> Self
    where
        T: Clone,
    {
        core::iter::repeat_n(element, count).collect()
    }

    /// Returns the number of elements in the list.
    #[must_use]
    pub const fn len(&self) -> usize {
        self.len
    }

    /// Returns `true` when the list contains no elements.
    #[must_use]
    pub const fn is_empty(&self) -> bool {
        self.len == 0
    }

    /// Returns a shared reference to the first element.
    #[must_use]
    pub fn front(&self) -> Option<&T> {
        self.head.as_deref().map(|node| &node.element)
    }

    /// Returns an exclusive reference to the first element.
    #[must_use]
    pub fn front_mut(&mut self) -> Option<&mut T> {
        self.head.as_deref_mut().map(|node| &mut node.element)
    }

    /// Returns a shared reference to the last element.
    ///
    /// This operation is `O(n)`.
    #[must_use]
    pub fn back(&self) -> Option<&T> {
        let mut current = self.head.as_deref()?;
        while let Some(next) = current.next.as_deref() {
            current = next;
        }
        Some(&current.element)
    }

    /// Returns an exclusive reference to the last element.
    ///
    /// This operation is `O(n)`.
    #[must_use]
    pub fn back_mut(&mut self) -> Option<&mut T> {
        let mut current = self.head.as_deref_mut()?;
        while let Some(next) = current.next.as_deref_mut() {
            current = next;
        }
        Some(&mut current.element)
    }

    /// Inserts an element at the front of the list in `O(1)`.
    pub fn push_front(&mut self, element: T) {
        let next = self.head.take();
        self.head = Some(Box::new(Node { element, next }));
        self.len += 1;
    }

    /// Removes and returns the first element in `O(1)`.
    pub fn pop_front(&mut self) -> Option<T> {
        self.head.take().map(|head| {
            let Node { element, next } = *head;
            self.head = next;
            self.len -= 1;
            element
        })
    }

    /// Inserts an element at the back of the list.
    ///
    /// This operation is `O(n)`. Use [`LinkedList::extend`] when adding several
    /// elements; one extension traverses the existing list only once.
    pub fn push_back(&mut self, element: T) {
        let mut tail = &mut self.head;
        while let Some(node) = tail {
            tail = &mut node.next;
        }
        *tail = Some(Box::new(Node {
            element,
            next: None,
        }));
        self.len += 1;
    }

    /// Removes and returns the last element.
    ///
    /// This operation is `O(n)`.
    pub fn pop_back(&mut self) -> Option<T> {
        let head = self.head.as_mut()?;
        if head.next.is_none() {
            return self.pop_front();
        }

        let mut current = head;
        while current
            .next
            .as_ref()
            .is_some_and(|next| next.next.is_some())
        {
            current = current
                .next
                .as_mut()
                .expect("the loop condition guarantees a next node");
        }

        let tail = current
            .next
            .take()
            .expect("a multi-element list has a tail node");
        self.len -= 1;
        Some(tail.element)
    }

    /// Moves all elements from `other` to the back of this list.
    ///
    /// `other` is empty after this operation. Existing nodes are relinked; no
    /// elements are cloned and no new nodes are allocated.
    pub fn append(&mut self, other: &mut Self) {
        if other.is_empty() {
            return;
        }

        let mut tail = &mut self.head;
        while let Some(node) = tail {
            tail = &mut node.next;
        }
        *tail = other.head.take();
        self.len += other.len;
        other.len = 0;
    }

    /// Removes every element from the list.
    ///
    /// Nodes are unlinked iteratively to avoid recursive destruction of a long
    /// chain.
    pub fn clear(&mut self) {
        let mut next = self.head.take();
        self.len = 0;
        while let Some(mut node) = next {
            next = node.next.take();
        }
    }

    /// Returns an iterator over shared references in front-to-back order.
    pub fn iter(&self) -> Iter<'_, T> {
        Iter {
            next: self.head.as_deref(),
            remaining: self.len,
        }
    }

    /// Returns an iterator over exclusive references in front-to-back order.
    pub fn iter_mut(&mut self) -> IterMut<'_, T> {
        IterMut {
            next: self.head.as_deref_mut(),
            remaining: self.len,
        }
    }
}

impl<T> Default for LinkedList<T> {
    fn default() -> Self {
        Self::new()
    }
}

impl<T> Drop for LinkedList<T> {
    fn drop(&mut self) {
        self.clear();
    }
}

impl<T: Clone> Clone for LinkedList<T> {
    fn clone(&self) -> Self {
        self.iter().cloned().collect()
    }

    fn clone_from(&mut self, source: &Self) {
        self.clear();
        self.extend(source.iter().cloned());
    }
}

impl<T: fmt::Debug> fmt::Debug for LinkedList<T> {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.debug_list().entries(self).finish()
    }
}

impl<T: PartialEq> PartialEq for LinkedList<T> {
    fn eq(&self, other: &Self) -> bool {
        self.len == other.len && self.iter().eq(other)
    }
}

impl<T: Eq> Eq for LinkedList<T> {}

impl<T: PartialOrd> PartialOrd for LinkedList<T> {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        self.iter().partial_cmp(other)
    }
}

impl<T: Ord> Ord for LinkedList<T> {
    fn cmp(&self, other: &Self) -> Ordering {
        self.iter().cmp(other)
    }
}

impl<T: Hash> Hash for LinkedList<T> {
    fn hash<H: Hasher>(&self, state: &mut H) {
        self.len.hash(state);
        for element in self {
            element.hash(state);
        }
    }
}

impl<T> Extend<T> for LinkedList<T> {
    fn extend<I: IntoIterator<Item = T>>(&mut self, iter: I) {
        let mut tail = &mut self.head;
        while let Some(node) = tail {
            tail = &mut node.next;
        }

        for element in iter {
            *tail = Some(Box::new(Node {
                element,
                next: None,
            }));
            tail = &mut tail
                .as_mut()
                .expect("a node was inserted immediately above")
                .next;
            self.len += 1;
        }
    }
}

impl<'a, T: Clone + 'a> Extend<&'a T> for LinkedList<T> {
    fn extend<I: IntoIterator<Item = &'a T>>(&mut self, iter: I) {
        self.extend(iter.into_iter().cloned());
    }
}

impl<T> FromIterator<T> for LinkedList<T> {
    fn from_iter<I: IntoIterator<Item = T>>(iter: I) -> Self {
        let mut list = Self::new();
        list.extend(iter);
        list
    }
}

impl<T, const N: usize> From<[T; N]> for LinkedList<T> {
    fn from(elements: [T; N]) -> Self {
        Self::from_array(elements)
    }
}

impl<T> IntoIterator for LinkedList<T> {
    type Item = T;
    type IntoIter = IntoIter<T>;

    fn into_iter(self) -> Self::IntoIter {
        IntoIter { list: self }
    }
}

impl<'a, T> IntoIterator for &'a LinkedList<T> {
    type Item = &'a T;
    type IntoIter = Iter<'a, T>;

    fn into_iter(self) -> Self::IntoIter {
        self.iter()
    }
}

impl<'a, T> IntoIterator for &'a mut LinkedList<T> {
    type Item = &'a mut T;
    type IntoIter = IterMut<'a, T>;

    fn into_iter(self) -> Self::IntoIter {
        self.iter_mut()
    }
}

/// An iterator that consumes a [`LinkedList`].
pub struct IntoIter<T> {
    list: LinkedList<T>,
}

impl<T> Iterator for IntoIter<T> {
    type Item = T;

    fn next(&mut self) -> Option<Self::Item> {
        self.list.pop_front()
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        (self.list.len, Some(self.list.len))
    }
}

impl<T> ExactSizeIterator for IntoIter<T> {}
impl<T> FusedIterator for IntoIter<T> {}

/// An iterator over shared references in a [`LinkedList`].
pub struct Iter<'a, T> {
    next: Option<&'a Node<T>>,
    remaining: usize,
}

impl<'a, T> Iterator for Iter<'a, T> {
    type Item = &'a T;

    fn next(&mut self) -> Option<Self::Item> {
        self.next.map(|node| {
            self.next = node.next.as_deref();
            self.remaining -= 1;
            &node.element
        })
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        (self.remaining, Some(self.remaining))
    }
}

impl<T> ExactSizeIterator for Iter<'_, T> {}
impl<T> FusedIterator for Iter<'_, T> {}

/// An iterator over exclusive references in a [`LinkedList`].
pub struct IterMut<'a, T> {
    next: Option<&'a mut Node<T>>,
    remaining: usize,
}

impl<'a, T> Iterator for IterMut<'a, T> {
    type Item = &'a mut T;

    fn next(&mut self) -> Option<Self::Item> {
        self.next.take().map(|node| {
            self.next = node.next.as_deref_mut();
            self.remaining -= 1;
            &mut node.element
        })
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        (self.remaining, Some(self.remaining))
    }
}

impl<T> ExactSizeIterator for IterMut<'_, T> {}
impl<T> FusedIterator for IterMut<'_, T> {}
