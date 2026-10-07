# Hardware review findings implementation plan

> **For agentic workers:** Use approved findings as the bounded implementation specification. Keep commits small and run the existing commit gate.

**Goal:** Close the six review passes' correctness and simplicity findings, regenerate PCB-dependent CAD, and deliver all pending work to main.

**Architecture:** Shared supplier and interface facts remain readable. The PCB owns placed electronics and exports a validated model; CAD consumes that model and verifies both the live assembly and saved artifact. Generic checks remain in each harness.

**Tech Stack:** Python, KiCad, Blender, Rust, pytest/unittest, GitHub Actions.

1. Add regressions for failed publication/rollback, incomplete GLB geometry, and source mutation. Repair publication and export validation.
2. Record the actual Blender version. Verify saved scenes, imported child placement, and small collisions. Polish floor/lighting without changing printed geometry.
3. Remove off-board wrapper classes, split discrete purchasing definitions, and move intrinsic supplier geometry beside those definitions.
4. Close harness net and firmware display parity; audit supporting supplier references. Run electrical suites once during review and prepare one CI container per hardware job.
5. Run focused checks, full PCB-to-CAD generation, native fit/artifact checks, repository precommit and independent review. Resolve failures.
6. Review and explicitly stage logical file groups, commit all authorized pending work, push, create/attach a PR if needed, merge with admin authorization, and verify clean main.
