use crate::model::{Command, Input, Menu, MenuItem};

use super::{event::Event, external::ExternalBehavior, snapshot::MenuSnapshot};

/// Maximum number of parent menus retained while navigating submenus.
pub const MAX_MENU_DEPTH: usize = 8;

struct Location<'a, A> {
    menu: &'a Menu<'a, A>,
    selected: usize,
}

/// Current location and cursor within a menu tree.
pub struct MenuState<'a, A> {
    root: &'a Menu<'a, A>,
    current: &'a Menu<'a, A>,
    selected: usize,
    depth: usize,
    history: [Option<Location<'a, A>>; MAX_MENU_DEPTH],
}

impl<'a, A> MenuState<'a, A> {
    /// Starts at the first entry of `root`.
    pub const fn new(root: &'a Menu<'a, A>) -> Self {
        Self {
            root,
            current: root,
            selected: 0,
            depth: 0,
            history: [const { None }; MAX_MENU_DEPTH],
        }
    }

    /// Returns the root menu supplied at construction.
    pub const fn root_menu(&self) -> &'a Menu<'a, A> {
        self.root
    }

    /// Returns the menu that a renderer should currently display.
    pub const fn current_menu(&self) -> &'a Menu<'a, A> {
        self.current
    }

    /// Returns the selected zero-based index.
    ///
    /// Empty menus also report zero; use [`Self::selected_item`] to distinguish
    /// that case.
    pub const fn selected_index(&self) -> usize {
        self.selected
    }

    /// Returns the selected entry, or `None` when the current menu is empty.
    pub fn selected_item(&self) -> Option<&'a MenuItem<'a, A>> {
        self.current.items().get(self.selected)
    }

    /// Returns the current submenu depth. The root menu is depth zero.
    pub const fn depth(&self) -> usize {
        self.depth
    }

    /// Returns a read-only view suitable for external behavior and renderers.
    pub const fn snapshot(&self) -> MenuSnapshot<'a, A> {
        MenuSnapshot::new(self.current, self.selected, self.depth)
    }

    /// Returns whether the root menu is currently displayed.
    pub const fn is_at_root(&self) -> bool {
        self.depth == 0
    }

    /// Applies one input using the current menu's controls.
    pub fn handle(&mut self, input: Input) -> Event<'a, A> {
        match self.current.controls().command(input) {
            Command::SelectPrevious => self.previous(),
            Command::SelectNext => self.next(),
            Command::Activate => self.activate(),
            Command::GoBack => self.back(),
            Command::Action(action) => Event::Activated(action),
            Command::Ignore => Event::Ignored,
        }
    }

    /// Applies input with an optional externally defined override.
    ///
    /// `context` is read-only, so a chess game can be passed directly without
    /// transferring ownership. The behavior remains mutable so it can own
    /// stateful hardware adapters. If it returns no command, the menu's normal
    /// controls are used.
    pub fn handle_with<C, B>(&mut self, input: Input, context: &C, behavior: &mut B) -> Event<'a, A>
    where
        C: ?Sized,
        B: ExternalBehavior<C, A> + ?Sized,
    {
        let Some(command) = behavior.on_input(context, self.snapshot(), input) else {
            return self.handle(input);
        };

        self.apply_external(command)
    }

    fn apply_external(&mut self, command: Command<A>) -> Event<'a, A> {
        match command {
            Command::SelectPrevious => self.previous(),
            Command::SelectNext => self.next(),
            Command::Activate => self.activate(),
            Command::GoBack => self.back(),
            Command::Action(action) => Event::ExternalAction(action),
            Command::Ignore => Event::Ignored,
        }
    }

    fn previous(&mut self) -> Event<'a, A> {
        if self.selected == 0 {
            return Event::Ignored;
        }

        self.selected -= 1;
        Event::SelectionChanged {
            selected: self.selected,
        }
    }

    fn next(&mut self) -> Event<'a, A> {
        if self.selected + 1 >= self.current.items().len() {
            return Event::Ignored;
        }

        self.selected += 1;
        Event::SelectionChanged {
            selected: self.selected,
        }
    }

    fn activate(&mut self) -> Event<'a, A> {
        let Some(item) = self.selected_item() else {
            return Event::Ignored;
        };

        match item {
            MenuItem::Action { action, .. } => Event::Activated(action),
            MenuItem::Submenu { menu, .. } => self.open(menu),
        }
    }

    fn open(&mut self, menu: &'a Menu<'a, A>) -> Event<'a, A> {
        if self.depth == MAX_MENU_DEPTH {
            return Event::DepthLimitReached;
        }

        self.history[self.depth] = Some(Location {
            menu: self.current,
            selected: self.selected,
        });
        self.depth += 1;
        self.current = menu;
        self.selected = 0;
        Event::Opened { depth: self.depth }
    }

    fn back(&mut self) -> Event<'a, A> {
        if self.depth == 0 {
            return Event::Ignored;
        }

        self.depth -= 1;
        let parent = self.history[self.depth]
            .take()
            .expect("every child menu has a saved parent");
        self.current = parent.menu;
        self.selected = parent.selected;
        Event::Closed { depth: self.depth }
    }
}
