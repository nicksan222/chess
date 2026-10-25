use crate::model::{Menu, MenuItem};

use super::{Location, MAX_MENU_DEPTH, MenuState};
use crate::navigation::event::Event;

impl<'a, A> MenuState<'a, A> {
    pub(super) fn previous(&mut self) -> Event<'a, A> {
        if self.selected == 0 {
            return Event::Ignored;
        }

        self.selected -= 1;
        Event::SelectionChanged {
            selected: self.selected,
        }
    }

    pub(super) fn next(&mut self) -> Event<'a, A> {
        if self.selected + 1 >= self.current.items().len() {
            return Event::Ignored;
        }

        self.selected += 1;
        Event::SelectionChanged {
            selected: self.selected,
        }
    }

    pub(super) fn activate(&mut self) -> Event<'a, A> {
        let Some(item) = self.selected_item() else {
            return Event::Ignored;
        };

        match item {
            MenuItem::Action { action, .. } => Event::Activated(action),
            MenuItem::BlockingAction {
                action,
                escape_action,
                ..
            } => self.begin_blocking(action, escape_action),
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

    pub(super) fn back(&mut self) -> Event<'a, A> {
        if self.depth == 0 {
            return Event::Ignored;
        }

        // Every opened child saved its parent, so the slot is always occupied.
        let Some(parent) = self.history[self.depth - 1].take() else {
            return Event::Ignored;
        };
        self.depth -= 1;
        self.current = parent.menu;
        self.selected = parent.selected;
        Event::Closed { depth: self.depth }
    }
}
