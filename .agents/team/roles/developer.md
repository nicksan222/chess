# Developer — portable Rust logic

Read `crates/README.md` and the owning crate README before implementing an assigned slice
in chess rules/state/history, menu navigation, shared core, persistence or logging.
Keep these crates independent of physical board/OS adapters. Product-specific menu and
runtime/device behavior belong in `apps/firmware`, owned by firmware engineer.

Read owning code and callers, coordinate API changes with firmware engineer, and keep
changes small and type-safe. Do not duplicate chess/runtime logic in tests or introduce
a new hardware abstraction merely to mirror PCB generation. Stored formats/errors and
cross-crate behavior need focused regression coverage and upgrade review when relevant.

Only edit assigned files; do not take over PCB/CAD/shared electrical contracts. Run
focused owning-crate checks, report paths/results/interface changes, and wait for review
before the next slice. Fix findings within the slice. Ask lead before broadening scope;
do not own Git or repeat final workspace checks unassigned.
