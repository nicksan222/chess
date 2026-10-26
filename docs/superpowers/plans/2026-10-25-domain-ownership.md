# Firmware Domain Ownership Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Keep domain values with their owners and communication mechanisms generic.

**Architecture:** Firmware reuses chess squares and square sets. Application menu bindings interpret physical button labels. The events module owns generic queues and latest-state channels, while domain modules own message payloads and state transitions.

**Tech Stack:** Rust, Tokio, Just, GitHub CLI stacks.

**Spec:** The user’s domain-ownership request; this document records its implementation scope.

## Global Constraints

Preserve sensor mappings, filtering, menu behavior, and snapshot acknowledgement. No physical hardware actions or merges. Keep #134 as the bottom PR and submit each follow-up against its predecessor using `gh stack`.

## Review Focus

- All 64 sensor channels retain their canonical square identity.
- Duplicate placement/removal preserves set semantics.
- Non-navigation buttons and releases stay inactive in menus.
- Latest-state updates survive missing readers and coalesce intermediate values.
- Snapshot waiting observes pending updates before channel closure.

### Task 1: Canonical chess values

- [ ] Change firmware integration tests to consume `chess::Square`; confirm the old event payload fails compilation.
- [ ] Replace `BoardPosition` and `square!` with `Square`; use `SquareSet` in pieces status and retain the existing numeric count API.
- [ ] Update both manifests, lockfiles, Yocto crate metadata, architecture guidance, and bank-contract tests as needed.
- [ ] Run firmware/shared checks, AArch64 linkage, isolated Yocto checks, and the commit gate; submit the layer.

### Task 2: Application button bindings

- [ ] Add literal mapping tests in `src/menu/input.rs`; verify the missing API fails compilation.
- [ ] Move `Button::menu_input` to `menu::input` and call it from runtime state.
- [ ] Run firmware checks and commit gate; submit the layer.

### Task 3: Generic latest-state communication

- [ ] Test generic latest-state publication, coalescing, late readers, and closure in `src/events/state.rs`.
- [ ] Implement typed publisher/subscriber wrappers, migrate runtime and pieces, and forbid raw Tokio watch channels outside events.
- [ ] Run firmware/quality checks and commit gate; obtain independent review and submit the layer.

## Delivery

Use `gh stack view` to verify the chain. Report the actual PR links in merge order; do not merge them.
