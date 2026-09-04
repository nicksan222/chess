import { describe, expect, test } from "bun:test";
import { changedPaths, selectChecks } from "../feedback/verification.js";

const cwd = "/repo";

describe("changedPaths", () => {
	test("finds additions, edits, and restorations without reporting unchanged dirty files", () => {
		const before = new Map([
			["already-dirty.rs", "same"],
			["edited.rs", "old"],
			["restored.rs", "dirty"],
		]);
		const after = new Map([
			["already-dirty.rs", "same"],
			["edited.rs", "new"],
			["new.rs", "content"],
		]);

		expect(changedPaths(before, after)).toEqual(["edited.rs", "new.rs", "restored.rs"]);
	});
});

describe("selectChecks", () => {
	test("uses a fast Cargo check for one Rust package", () => {
		const checks = selectChecks(cwd, ["crates/chess/src/lib.rs"], "fast");

		expect(checks).toHaveLength(1);
		expect(checks[0]?.id).toBe("crates/chess:cargo-check");
		expect(checks[0]?.command).toBe("cargo");
		expect(checks[0]?.args).toContain("chess");
	});

	test("deduplicates checks for files in the same package", () => {
		const checks = selectChecks(
			cwd,
			["crates/chess/src/lib.rs", "crates/chess/src/engine/search.rs"],
			"test",
		);

		expect(checks.map((check) => check.id)).toEqual(["crates/chess:test"]);
	});

	test("runs each affected package in stable order", () => {
		const checks = selectChecks(
			cwd,
			["hardware/pcb/generate.py", "crates/core/src/lib.rs"],
			"fast",
		);

		expect(checks.map((check) => check.id)).toEqual([
			"crates/core:cargo-check",
			"hardware/pcb:quality",
		]);
	});

	test("validates Pi extension changes with the Bun project", () => {
		const checks = selectChecks(cwd, [".pi/extensions/change-tracker/index.ts"], "fast");

		expect(checks.map((check) => check.id)).toEqual([".pi:check"]);
		expect(checks[0]?.args).toEqual(["run", "--cwd", "/repo/.pi", "check"]);
	});

	test("uses a non-invasive diff check for unscoped fast validation", () => {
		const checks = selectChecks(cwd, ["justfile"], "fast");

		expect(checks.map((check) => check.id)).toEqual(["repository:diff-check"]);
		expect(checks[0]?.command).toBe("git");
	});

	test("keeps scoped checks when a change set also has unscoped paths", () => {
		const checks = selectChecks(cwd, [".pi/extensions/change-tracker/index.ts", ".devcontainer/devcontainer.json"], "full");

		expect(checks.map((check) => check.id)).toEqual([".pi:check", "repository:precommit"]);
	});

	test("avoids PCB previews during full changed-file validation", () => {
		const checks = selectChecks(cwd, ["hardware/pcb/generate.py"], "full");

		expect(checks.map((check) => check.id)).toEqual(["hardware/pcb:check-fast"]);
	});
});
