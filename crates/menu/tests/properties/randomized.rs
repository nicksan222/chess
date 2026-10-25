use std::collections::BTreeSet;

use menu::{Command, Event, ExternalBehavior, Input, MenuCallbacks, MenuSnapshot, MenuState};

use crate::fixture::{Act, OPS, Op, ROOT};
use crate::reference::Reference;

const SEEDS: u64 = 512;
const STEPS: usize = 512;

#[derive(Clone, Copy)]
struct XorShift64(u64);

impl XorShift64 {
    fn new(seed: u64) -> Self {
        Self(0x9e37_79b9_7f4a_7c15_u64.wrapping_mul(seed + 1))
    }

    fn next(&mut self) -> u64 {
        self.0 ^= self.0 << 13;
        self.0 ^= self.0 >> 7;
        self.0 ^= self.0 << 17;
        self.0
    }

    fn below(&mut self, bound: usize) -> usize {
        let bound = u64::try_from(bound).expect("bounds fit in u64");
        usize::try_from(self.next() % bound).expect("a value below a usize bound fits in usize")
    }
}

/// How one step reaches the menu.
#[derive(Clone, Copy, Debug)]
enum Entry {
    Handle,
    HandleAndDispatch,
    HandleWith,
    HandleWithAndDispatch,
}

const ENTRIES: [Entry; 4] = [
    Entry::Handle,
    Entry::HandleAndDispatch,
    Entry::HandleWith,
    Entry::HandleWithAndDispatch,
];

/// An external behavior whose answer is chosen by the test before each input.
#[derive(Default)]
struct Scripted {
    answer: Option<Command<Act>>,
    calls: usize,
    seen: Option<(usize, usize, bool)>,
}

impl ExternalBehavior<u64, Act> for Scripted {
    fn on_input(
        &mut self,
        _context: &u64,
        menu: MenuSnapshot<'_, Act>,
        _input: Input,
    ) -> Option<Command<Act>> {
        self.calls += 1;
        self.seen = Some((menu.depth(), menu.selected_index(), menu.is_blocked()));
        self.answer.take()
    }
}

/// Counts callbacks so every dispatch can be checked against its event.
#[derive(Default)]
struct Counts {
    actions: usize,
    starts: usize,
    aborts: usize,
}

impl MenuCallbacks<Act> for Counts {
    fn on_action(&mut self, _action: &Act) {
        self.actions += 1;
    }

    fn on_blocking_started(&mut self, _action: &Act) {
        self.starts += 1;
    }

    fn on_blocking_aborted(&mut self, _operation: &Act, _escape_action: &Act) {
        self.aborts += 1;
    }
}

fn random_answer(random: &mut XorShift64) -> Option<Command<Act>> {
    match random.below(8) {
        0 => Some(Command::SelectPrevious),
        1 => Some(Command::SelectNext),
        2 => Some(Command::Activate),
        3 => Some(Command::GoBack),
        4 => Some(Command::Action(Act("external"))),
        5 => Some(Command::Ignore),
        _ => None,
    }
}

fn kind(event: &Event<'_, Act>) -> &'static str {
    match event {
        Event::SelectionChanged { .. } => "SelectionChanged",
        Event::Opened { .. } => "Opened",
        Event::Closed { .. } => "Closed",
        Event::Activated(_) => "Activated",
        Event::BlockingStarted(_) => "BlockingStarted",
        Event::BlockingAborted { .. } => "BlockingAborted",
        Event::InputBlocked => "InputBlocked",
        Event::ExternalAction(_) => "ExternalAction",
        Event::Ignored => "Ignored",
        Event::DepthLimitReached => "DepthLimitReached",
    }
}

const EVERY_KIND: [&str; 10] = [
    "SelectionChanged",
    "Opened",
    "Closed",
    "Activated",
    "BlockingStarted",
    "BlockingAborted",
    "InputBlocked",
    "ExternalAction",
    "Ignored",
    "DepthLimitReached",
];

type Observed = (usize, usize, bool);

/// The behavior is consulted exactly when an override entry point is used
/// outside a blocking operation, and sees the state before input. Returns the
/// state it is expected to have seen, or `None` when it must not be consulted.
fn expected_sighting(entry: Entry, before: Observed) -> Option<Observed> {
    let consulted = matches!(entry, Entry::HandleWith | Entry::HandleWithAndDispatch) && !before.2;
    consulted.then_some(before)
}

fn assert_behavior_consulted(
    behavior: &Scripted,
    calls_before: usize,
    expected: Option<Observed>,
    context: &str,
) {
    assert_eq!(
        behavior.calls - calls_before,
        usize::from(expected.is_some()),
        "{context}"
    );
    if expected.is_some() {
        assert_eq!(behavior.seen, expected, "{context}");
    }
}

/// Dispatching entry points invoke exactly the callback the event names.
fn expected_dispatch(entry: Entry, event: &Event<'_, Act>) -> (usize, usize, usize) {
    let dispatched = matches!(
        entry,
        Entry::HandleAndDispatch | Entry::HandleWithAndDispatch
    );
    match (event, dispatched) {
        (Event::Activated(_) | Event::ExternalAction(_), true) => (1, 0, 0),
        (Event::BlockingStarted(_), true) => (0, 1, 0),
        (Event::BlockingAborted { .. }, true) => (0, 0, 1),
        _ => (0, 0, 0),
    }
}

fn assert_dispatch(
    counts: &Counts,
    before_counts: (usize, usize, usize),
    expected: (usize, usize, usize),
    context: &str,
) {
    assert_eq!(
        (
            counts.actions - before_counts.0,
            counts.starts - before_counts.1,
            counts.aborts - before_counts.2,
        ),
        expected,
        "{context}"
    );
}

#[test]
fn long_random_sessions_through_every_entry_point_match_the_reference() {
    let mut reached = BTreeSet::new();

    for seed in 0..SEEDS {
        let mut random = XorShift64::new(seed);
        let mut state = MenuState::new(&ROOT);
        let mut reference = Reference::new(&ROOT);
        let mut behavior = Scripted::default();
        let mut counts = Counts::default();

        for step in 0..STEPS {
            let context = format!("seed {seed}, step {step}");
            let input = match OPS[random.below(OPS.len())] {
                Op::Press(input) => input,
                Op::Unblock => {
                    assert_eq!(state.unblock(), reference.unblock(), "{context}");
                    reference.assert_matches(&state, &context);
                    continue;
                }
            };
            let entry = ENTRIES[random.below(ENTRIES.len())];
            let context = format!("{context}, {entry:?}({input:?})");

            let before = (state.depth(), state.selected_index(), state.is_blocked());
            let calls_before = behavior.calls;
            // `Command` is not `Clone`, so draw the same answer twice.
            let mut twin = random;
            let answer = random_answer(&mut random);
            let expected = match entry {
                Entry::Handle | Entry::HandleAndDispatch => reference.press(input),
                Entry::HandleWith | Entry::HandleWithAndDispatch => {
                    reference.press_with(input, random_answer(&mut twin))
                }
            };
            behavior.answer = answer;
            behavior.seen = None;

            let before_counts = (counts.actions, counts.starts, counts.aborts);
            let event = match entry {
                Entry::Handle => state.handle(input),
                Entry::HandleAndDispatch => state.handle_and_dispatch(input, &mut counts),
                Entry::HandleWith => state.handle_with(input, &seed, &mut behavior),
                Entry::HandleWithAndDispatch => {
                    state.handle_with_and_dispatch(input, &seed, &mut behavior, &mut counts)
                }
            };

            assert_eq!(event, expected, "{context}");
            reference.assert_matches(&state, &context);
            reached.insert(kind(&event));

            let sighting = expected_sighting(entry, before);
            assert_behavior_consulted(&behavior, calls_before, sighting, &context);
            let dispatch = expected_dispatch(entry, &event);
            assert_dispatch(&counts, before_counts, dispatch, &context);
        }
    }

    // Guard against the generator silently drifting away from parts of the
    // state space, which would weaken this test without failing it.
    let missing: Vec<_> = EVERY_KIND
        .into_iter()
        .filter(|kind| !reached.contains(kind))
        .collect();
    assert!(missing.is_empty(), "never produced {missing:?}");
}
