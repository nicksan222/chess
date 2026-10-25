use menu::{Command, Event, Input, MAX_MENU_DEPTH, Menu, MenuItem, MenuState};

use crate::fixture::Act;

/// The documented menu behavior, written as directly as possible.
///
/// `path` holds every open menu with its cursor; the last entry is the menu on
/// screen. Unlike `MenuState` it uses an unbounded `Vec`, so the depth limit is
/// an explicit rule rather than a storage constraint.
pub(crate) struct Reference<'a> {
    root: &'a Menu<'a, Act>,
    path: Vec<(&'a Menu<'a, Act>, usize)>,
    blocking: Option<(&'a Act, &'a Act)>,
}

impl<'a> Reference<'a> {
    pub(crate) fn new(root: &'a Menu<'a, Act>) -> Self {
        Self {
            root,
            path: vec![(root, 0)],
            blocking: None,
        }
    }

    pub(crate) fn menu(&self) -> &'a Menu<'a, Act> {
        self.path.last().expect("the root is never closed").0
    }

    pub(crate) fn selected(&self) -> usize {
        self.path.last().expect("the root is never closed").1
    }

    pub(crate) fn depth(&self) -> usize {
        self.path.len() - 1
    }

    /// `MenuState::handle`.
    pub(crate) fn press(&mut self, input: Input) -> Event<'a, Act> {
        if let Some(event) = self.while_blocked(input) {
            return event;
        }

        match self.menu().controls().command(input) {
            Command::Action(action) => Event::Activated(action),
            command => self.navigate(command),
        }
    }

    /// `MenuState::handle_with`, given what the external behavior answered.
    pub(crate) fn press_with(
        &mut self,
        input: Input,
        answer: Option<Command<Act>>,
    ) -> Event<'a, Act> {
        if let Some(event) = self.while_blocked(input) {
            return event;
        }

        match answer {
            None => self.press(input),
            Some(Command::Action(action)) => Event::ExternalAction(action),
            Some(command) => self.navigate(&command),
        }
    }

    /// `MenuState::unblock`.
    pub(crate) fn unblock(&mut self) -> Option<&'a Act> {
        self.blocking.take().map(|(action, _)| action)
    }

    fn while_blocked(&mut self, input: Input) -> Option<Event<'a, Act>> {
        let (operation, escape_action) = self.blocking?;

        if input == Input::Escape {
            self.blocking = None;
            Some(Event::BlockingAborted {
                operation,
                escape_action,
            })
        } else {
            Some(Event::InputBlocked)
        }
    }

    fn navigate(&mut self, command: &Command<Act>) -> Event<'a, Act> {
        let menu = self.menu();
        let selected = self.selected();
        let count = menu.items().len();

        match command {
            Command::SelectPrevious if selected > 0 => self.select(selected - 1),
            Command::SelectNext if selected + 1 < count => self.select(selected + 1),
            Command::Activate => match menu.items().get(selected) {
                None => Event::Ignored,
                Some(MenuItem::Action { action, .. }) => Event::Activated(action),
                Some(MenuItem::BlockingAction {
                    action,
                    escape_action,
                    ..
                }) => {
                    self.blocking = Some((action, escape_action));
                    Event::BlockingStarted(action)
                }
                Some(MenuItem::Submenu { .. }) if self.depth() == MAX_MENU_DEPTH => {
                    Event::DepthLimitReached
                }
                Some(MenuItem::Submenu { menu: child, .. }) => {
                    self.path.push((child, 0));
                    Event::Opened {
                        depth: self.depth(),
                    }
                }
            },
            Command::GoBack if self.depth() > 0 => {
                self.path.pop();
                Event::Closed {
                    depth: self.depth(),
                }
            }
            Command::Action(_) => unreachable!("actions never navigate"),
            _ => Event::Ignored,
        }
    }

    fn select(&mut self, index: usize) -> Event<'a, Act> {
        self.path.last_mut().expect("the root is never closed").1 = index;
        Event::SelectionChanged { selected: index }
    }

    /// Asserts every observable property of `state` against this reference,
    /// plus invariants that must hold regardless of history.
    pub(crate) fn assert_matches(
        &self,
        state: &MenuState<'a, Act>,
        context: &dyn core::fmt::Display,
    ) {
        self.assert_state(state, context);
        self.assert_snapshot(state, context);
    }

    fn assert_state(&self, state: &MenuState<'a, Act>, context: &dyn core::fmt::Display) {
        let blocking_action = self.blocking.map(|(action, _)| action);
        let escape_action = self.blocking.map(|(_, escape)| escape);

        assert!(core::ptr::eq(state.root_menu(), self.root), "{context}");
        assert!(
            core::ptr::eq(state.current_menu(), self.menu()),
            "{context}: showing {:?}, expected {:?}",
            state.current_menu().title(),
            self.menu().title()
        );
        assert_eq!(state.selected_index(), self.selected(), "{context}");
        assert_eq!(state.depth(), self.depth(), "{context}");
        assert_eq!(state.is_at_root(), self.depth() == 0, "{context}");
        assert_eq!(state.is_blocked(), self.blocking.is_some(), "{context}");
        assert_eq!(state.blocking_action(), blocking_action, "{context}");
        assert_eq!(state.blocking_escape_action(), escape_action, "{context}");

        let count = state.current_menu().items().len();
        assert!(state.depth() <= MAX_MENU_DEPTH, "{context}");
        assert!(
            state.selected_index() < count || (count == 0 && state.selected_index() == 0),
            "{context}: cursor {} outside {count} entries",
            state.selected_index()
        );
        assert!(
            same_item(
                state.selected_item(),
                state.current_menu().items().get(state.selected_index())
            ),
            "{context}"
        );
    }

    fn assert_snapshot(&self, state: &MenuState<'a, Act>, context: &dyn core::fmt::Display) {
        let blocking_action = self.blocking.map(|(action, _)| action);
        let escape_action = self.blocking.map(|(_, escape)| escape);

        let snapshot = state.snapshot();
        assert!(
            core::ptr::eq(snapshot.menu(), state.current_menu()),
            "{context}"
        );
        assert_eq!(
            snapshot.selected_index(),
            state.selected_index(),
            "{context}"
        );
        assert!(
            same_item(snapshot.selected_item(), state.selected_item()),
            "{context}"
        );
        assert_eq!(snapshot.depth(), state.depth(), "{context}");
        assert_eq!(snapshot.is_blocked(), state.is_blocked(), "{context}");
        assert_eq!(snapshot.blocking_action(), blocking_action, "{context}");
        assert_eq!(
            snapshot.blocking_escape_action(),
            escape_action,
            "{context}"
        );
    }
}

/// Compares entries by identity. Derived equality on `MenuItem` follows
/// submenus structurally and never terminates on this fixture's cyclic tree.
fn same_item(left: Option<&MenuItem<'_, Act>>, right: Option<&MenuItem<'_, Act>>) -> bool {
    match (left, right) {
        (Some(left), Some(right)) => core::ptr::eq(left, right),
        (None, None) => true,
        _ => false,
    }
}
