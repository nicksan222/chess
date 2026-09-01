use crate::model::{Menu, MenuItem};

/// Read-only view of the current menu location.
pub struct MenuSnapshot<'a, A> {
    menu: &'a Menu<'a, A>,
    selected: usize,
    depth: usize,
}

impl<'a, A> MenuSnapshot<'a, A> {
    pub(super) const fn new(menu: &'a Menu<'a, A>, selected: usize, depth: usize) -> Self {
        Self {
            menu,
            selected,
            depth,
        }
    }

    /// Returns the menu receiving the input.
    pub const fn menu(&self) -> &'a Menu<'a, A> {
        self.menu
    }

    /// Returns the selected zero-based index.
    ///
    /// Empty menus also report zero; use [`Self::selected_item`] to distinguish
    /// that case.
    pub const fn selected_index(&self) -> usize {
        self.selected
    }

    /// Returns the selected item, or `None` for an empty menu.
    pub fn selected_item(&self) -> Option<&'a MenuItem<'a, A>> {
        self.menu.items().get(self.selected)
    }

    /// Returns the current depth, where the root menu is depth zero.
    pub const fn depth(&self) -> usize {
        self.depth
    }
}

impl<A> Clone for MenuSnapshot<'_, A> {
    fn clone(&self) -> Self {
        *self
    }
}

impl<A> Copy for MenuSnapshot<'_, A> {}
