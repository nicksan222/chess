/// Observable result of applying input to a menu state.
#[must_use = "menu events may contain actions that the application must handle"]
#[derive(Debug, Eq, PartialEq)]
pub enum Event<'a, A> {
    /// The selected entry changed.
    SelectionChanged {
        /// New zero-based index within the current menu.
        selected: usize,
    },
    /// A child menu was opened.
    Opened {
        /// New depth, where the root menu is depth zero.
        depth: usize,
    },
    /// The parent menu was restored.
    Closed {
        /// New depth, where the root menu is depth zero.
        depth: usize,
    },
    /// An action stored in a menu or its controls was requested.
    Activated(&'a A),
    /// An action produced by external behavior was requested.
    ExternalAction(A),
    /// The command could not change the current state.
    Ignored,
    /// A submenu could not open because the navigation depth limit was reached.
    DepthLimitReached,
}
