//! Self-contained firmware modules, each behind its own facade.
//!
//! Every module is a folder here whose `mod.rs` is the facade; implementation
//! files stay private, which `unreachable_pub` enforces. Modules are
//! registered with one line below, in dependency order; `module.rs` holds the
//! contract. Menu requests without an integration yet are placeholders that
//! finish immediately.

#![deny(unreachable_pub)]

mod module;
mod registry;

pub(crate) use module::report;
pub use module::{Facade, MissingDependency, ModuleEvent, ModuleEventBus, Never, Phase};

registry::modules! {
    /// Wi-Fi status, scanning and provisioning.
    connection: Connection,
    /// Firmware update discovery; uses `connection`.
    firmware: Updates,
    /// Game setup.
    play: Play,
    /// Pairing and online sessions.
    pairing: Pairing,
    /// Piece presence on the board; it has no menu items.
    pieces: Pieces,
}

#[cfg(test)]
mod tests {
    use ::menu::{Event, Input, Menu, MenuItem, MenuState};

    use super::*;
    use crate::menu::MAIN_MENU;

    fn leaves() -> Vec<&'static MenuItem<'static, Request>> {
        fn walk(
            menu: &'static Menu<'static, Request>,
            found: &mut Vec<&'static MenuItem<'static, Request>>,
        ) {
            for item in menu.items() {
                match item.as_submenu() {
                    Some(submenu) => walk(submenu, found),
                    None => found.push(item),
                }
            }
        }
        let mut found = Vec::new();
        walk(&MAIN_MENU, &mut found);
        found
    }

    #[test]
    fn a_blocking_item_is_cancelled_by_the_module_that_runs_it() {
        for item in leaves() {
            let request = item.as_action().expect("menu leaves are actions");
            if let Some(cancel) = item.escape_action() {
                assert!(item.is_blocking(), "{request:?}");
                assert_eq!(cancel.module(), request.module(), "{request:?}");
            }
        }
    }

    #[test]
    fn no_request_is_offered_twice() {
        let mut offered: Vec<Request> = leaves()
            .into_iter()
            .flat_map(|item| [item.as_action().copied(), item.escape_action().copied()])
            .flatten()
            .collect();
        let count = offered.len();
        offered.sort_by_key(|request| format!("{request:?}"));
        offered.dedup();
        assert_eq!(offered.len(), count);
    }

    #[test]
    fn the_registry_builds_every_module_offline_and_as_the_device() {
        // Building reaches no network: NetworkManager is lazy and the release
        // feed is read only by a check.
        for config in [Config::offline(), Config::device()] {
            let (_, facades) = Modules::new(&config, &ModuleEventBus::new())
                .unwrap_or_else(|error| panic!("{config:?}: {error}"));
            for module in REGISTERED {
                assert!((module.built)(&facades), "{} was not built", module.name);
            }
        }
        assert_eq!(<firmware::Updates as Facade>::MODULE, "firmware");
    }

    #[test]
    fn every_module_with_requests_has_its_menu_in_the_main_menu() {
        for module in REGISTERED {
            let Some(menu) = module.menu else {
                assert!(
                    !(module.has_requests)(),
                    "{} has requests but no MENU",
                    module.name
                );
                continue;
            };
            assert!(
                MAIN_MENU.items().iter().any(|item| item
                    .as_submenu()
                    .is_some_and(|listed| std::ptr::eq(listed, menu))),
                "{}::MENU is not listed in menu/definition.rs",
                module.name
            );
            for item in menu.items() {
                let request = item.as_action().expect("module menus hold actions");
                assert_eq!(request.module(), module.name, "{request:?}");
            }
        }
    }

    #[test]
    fn requests_name_their_module() {
        assert_eq!(
            Request::Updates(firmware::Request::Check).module(),
            "firmware"
        );
        assert_eq!(Request::Play(play::Request::LocalGame).module(), "play");
        assert_eq!(
            Request::Connection(connection::Request::ScanWifi).module(),
            "connection"
        );
    }

    #[test]
    fn only_a_finished_report_for_the_blocking_request_releases_the_menu() {
        const CHECK: Request = Request::Updates(firmware::Request::Check);
        const INSTALL: Request = Request::Updates(firmware::Request::Install);
        static BLOCKING: Menu<'static, Request> = Menu::new(
            "Test",
            &[MenuItem::blocking_action(
                "Check",
                CHECK,
                Request::Updates(firmware::Request::CancelCheck),
            )],
        );
        let event = |request, phase| {
            ModuleEvent::new::<firmware::Updates>(Some(request), phase, firmware::Status::UpToDate)
        };
        let mut menu = MenuState::new(&BLOCKING);
        let mut status = ModuleStatus::default();
        assert_eq!(menu.handle(Input::Ok), Event::BlockingStarted(&CHECK));

        report(event(CHECK, Phase::Progress), &mut menu, &mut status);
        assert!(menu.is_blocked());
        report(event(INSTALL, Phase::Finished), &mut menu, &mut status);
        assert!(menu.is_blocked());
        report(
            ModuleEvent::new::<firmware::Updates>(
                None,
                Phase::Finished,
                firmware::Status::UpToDate,
            ),
            &mut menu,
            &mut status,
        );
        assert!(menu.is_blocked(), "work no request started never unblocks");
        report(event(CHECK, Phase::Finished), &mut menu, &mut status);
        assert!(!menu.is_blocked());
        assert_eq!(status.firmware, firmware::Status::UpToDate);
    }

    #[test]
    fn a_report_without_a_status_keeps_the_last_one() {
        static EMPTY: Menu<'static, Request> = Menu::new("Empty", &[]);
        let events = ModuleEventBus::new();
        let mut reports = events.subscribe();
        let mut menu = MenuState::new(&EMPTY);
        let mut status = ModuleStatus {
            firmware: firmware::Status::UpToDate,
            ..ModuleStatus::default()
        };

        module::Reporter::new(
            &events,
            Some(Request::Updates(firmware::Request::Install)),
            <firmware::Updates as module::sealed::Registered>::wrap,
        )
        .done();
        report(reports.try_recv().unwrap().unwrap(), &mut menu, &mut status);

        assert_eq!(status.firmware, firmware::Status::UpToDate);
    }
}
