use super::{MenuControls, MenuItem};

/// Read-only menu data required by a renderer or other menu consumer.
pub trait MenuDefinition<'a, A> {
    /// Returns the menu title.
    fn title(&self) -> &'a str;

    /// Returns entries in display order.
    fn items(&self) -> &[MenuItem<'a, A>];

    /// Returns this menu's button behavior.
    fn controls(&self) -> &MenuControls<A>;
}

/// A menu, its ordered entries, and its input behavior.
#[derive(Debug, Eq, PartialEq)]
pub struct Menu<'a, A> {
    title: &'a str,
    items: &'a [MenuItem<'a, A>],
    controls: MenuControls<A>,
}

impl<'a, A> Menu<'a, A> {
    /// Creates a menu with conventional vertical-list controls.
    pub const fn new(title: &'a str, items: &'a [MenuItem<'a, A>]) -> Self {
        Self::with_controls(title, items, MenuControls::list())
    }

    /// Creates a menu with explicit behavior for every menu button.
    pub const fn with_controls(
        title: &'a str,
        items: &'a [MenuItem<'a, A>],
        controls: MenuControls<A>,
    ) -> Self {
        Self {
            title,
            items,
            controls,
        }
    }

    /// Returns the title shown above this menu's entries.
    pub const fn title(&self) -> &'a str {
        self.title
    }

    /// Returns this menu's entries in display order.
    pub const fn items(&self) -> &'a [MenuItem<'a, A>] {
        self.items
    }

    /// Returns this menu's button behavior.
    pub const fn controls(&self) -> &MenuControls<A> {
        &self.controls
    }

    /// Returns whether this menu contains no entries.
    pub const fn is_empty(&self) -> bool {
        self.items.is_empty()
    }
}

impl<'a, A> MenuDefinition<'a, A> for Menu<'a, A> {
    fn title(&self) -> &'a str {
        self.title
    }

    fn items(&self) -> &[MenuItem<'a, A>] {
        self.items
    }

    fn controls(&self) -> &MenuControls<A> {
        &self.controls
    }
}
