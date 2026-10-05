//! Drives the production menu by intent: tests name a `Request`, and the button
//! presses that reach it are derived from the product menu definition.

use firmware::{
    hardware::pins::{Button, ButtonEvent},
    harness::FirmwareHarness,
    menu::{MAIN_MENU, Request},
    runtime::Snapshot,
};
use menu::{Menu, MenuItem};

const MAX_PRESSES: usize = 16;

pub struct Navigator {
    pub firmware: FirmwareHarness,
    snapshot: Snapshot,
}

impl Navigator {
    pub fn start() -> Self {
        let firmware = FirmwareHarness::start().unwrap();
        let snapshot = firmware.snapshot();
        Self { firmware, snapshot }
    }

    /// Returns to the main menu, then selects and activates `request`.
    pub async fn open(&mut self, request: Request) -> Snapshot {
        let path = path_to(&MAIN_MENU, request)
            .unwrap_or_else(|| panic!("{request:?} is not reachable from the main menu"));
        // Every loop is bounded so a stuck menu fails the test instead of hanging it.
        for _ in 0..MAX_PRESSES {
            if self.snapshot.menu_depth == 0 {
                break;
            }
            self.press(Button::Left).await;
        }
        assert_eq!(
            self.snapshot.menu_depth, 0,
            "Left did not return to the main menu"
        );
        for index in path {
            for _ in 0..MAX_PRESSES {
                if self.snapshot.selected_index == index {
                    break;
                }
                let towards = if self.snapshot.selected_index < index {
                    Button::Down
                } else {
                    Button::Up
                };
                self.press(towards).await;
            }
            assert_eq!(
                self.snapshot.selected_index, index,
                "could not select menu item {index} for {request:?}"
            );
            self.press(Button::Ok).await; // Opens a submenu or activates a leaf.
        }
        self.snapshot.clone()
    }

    async fn press(&mut self, button: Button) {
        self.snapshot = self
            .firmware
            .trigger(ButtonEvent::Pressed(button))
            .await
            .unwrap();
    }
}

/// Every request the product menu exposes, in menu order.
pub fn every_request() -> Vec<Request> {
    let mut found = Vec::new();
    collect(&MAIN_MENU, &mut found);
    found
}

fn collect(menu: &Menu<'static, Request>, found: &mut Vec<Request>) {
    for item in menu.items() {
        match (item.as_action(), item.as_submenu()) {
            (Some(request), _) => found.push(*request),
            (_, Some(submenu)) => collect(submenu, found),
            _ => {}
        }
    }
}

/// Item indices from the root to the leaf that requests `request`.
fn path_to(menu: &Menu<'static, Request>, request: Request) -> Option<Vec<usize>> {
    menu.items().iter().enumerate().find_map(|(index, item)| {
        let rest = leaf_path(item, request)?;
        Some([vec![index], rest].concat())
    })
}

fn leaf_path(item: &MenuItem<'static, Request>, request: Request) -> Option<Vec<usize>> {
    match (item.as_action(), item.as_submenu()) {
        (Some(found), _) if *found == request => Some(Vec::new()),
        (_, Some(submenu)) => path_to(submenu, request),
        _ => None,
    }
}
