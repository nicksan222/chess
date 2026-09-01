use super::Menu;

/// One selectable menu entry.
#[derive(Debug, Eq, PartialEq)]
pub enum MenuItem<'a, A> {
    /// An entry that produces an application-defined action when activated.
    Action {
        /// Text presented for the entry.
        label: &'a str,
        /// Value returned to the application on activation.
        action: A,
    },
    /// An entry that opens another menu when activated.
    Submenu {
        /// Text presented for the entry.
        label: &'a str,
        /// Child menu opened on activation.
        menu: &'a Menu<'a, A>,
    },
}

impl<'a, A> MenuItem<'a, A> {
    /// Creates an entry that emits `action` when activated.
    pub const fn action(label: &'a str, action: A) -> Self {
        Self::Action { label, action }
    }

    /// Creates an entry that opens `menu` when activated.
    pub const fn submenu(label: &'a str, menu: &'a Menu<'a, A>) -> Self {
        Self::Submenu { label, menu }
    }

    /// Returns the text presented for this entry.
    pub const fn label(&self) -> &'a str {
        match self {
            Self::Action { label, .. } | Self::Submenu { label, .. } => label,
        }
    }

    /// Returns the action carried by this entry, if it is an action entry.
    pub const fn as_action(&self) -> Option<&A> {
        match self {
            Self::Action { action, .. } => Some(action),
            Self::Submenu { .. } => None,
        }
    }

    /// Returns the child menu carried by this entry, if it is a submenu entry.
    pub const fn as_submenu(&self) -> Option<&'a Menu<'a, A>> {
        match self {
            Self::Action { .. } => None,
            Self::Submenu { menu, .. } => Some(menu),
        }
    }
}
