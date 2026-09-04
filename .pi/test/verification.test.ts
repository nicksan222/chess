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

	test("uses manifest package names for renamed workspace crates", () => {
		for (const [path, packageName] of [
			["apps/simulator/src/main.rs", "chess-simulator"],
			["crates/core/src/lib.rs", "chess-core"],
		] as const) {
			const check = selectChecks(cwd, [path], "fast")[0];
			expect(check?.args).toContain(packageName);
		}
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

	test("runs firmware quality checks for Yocto Python changes", () => {
		const checks = selectChecks(cwd, ["apps/firmware/yocto/validate_crates.py"], "fast");

		expect(checks.map((check) => check.id)).toEqual(["apps/firmware:quality"]);
		expect(checks[0]?.command).toBe("just");
	});

	test("dry-runs BitBake for Yocto metadata changes", () => {
		for (const level of ["fast", "full"] as const) {
			const checks = selectChecks(cwd, ["apps/firmware/yocto/kas/firmware.yml"], level);
			expect(checks[0]?.id).toBe("apps/firmware:image-check");
		}
	});

	test("validates Pi extension changes with the Bun project", () => {
		const checks = selectChecks(cwd, [".pi/extensions/change-tracker/index.ts"], "fast");

		expect(checks.map((check) => check.id)).toEqual([".pi:check"]);
		expect(checks[0]?.args).toEqual(["run", "--cwd", "/repo/.pi", "check"]);
	});

	test("routes CI and devcontainer configuration through the Pi harness", () => {
		for (const path of [".github/workflows/ci.yml", ".devcontainer/devcontainer.json"]) {
			expect(selectChecks(cwd, [path], "fast").map((check) => check.id)).toEqual([".pi:check"]);
		}
	});

	test("checks devcontainer shell syntax alongside Pi configuration", () => {
		const checks = selectChecks(cwd, [".devcontainer/post-create.sh"], "fast");

		expect(checks.map((check) => check.id)).toEqual([
			".pi:check",
			".devcontainer/post-create.sh:bash-syntax",
		]);
	});

	test("checks root Cargo metadata across the workspace", () => {
		for (const path of ["Cargo.toml", "Cargo.lock"]) {
			const checks = selectChecks(cwd, [path], "fast");
			expect(checks.map((check) => check.id)).toEqual(["workspace:cargo-check"]);
			expect(checks[0]?.args).toContain("--workspace");
		}
		expect(selectChecks(cwd, ["Cargo.toml"], "full").map((check) => check.id)).toEqual([
			"repository:precommit",
		]);
		expect(selectChecks(cwd, ["Cargo.toml", ".pi/package.json"], "full").map((check) => check.id)).toEqual([
			".pi:check",
			"repository:precommit",
		]);
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

	test("adds the repository gate for reverse dependents during full validation", () => {
		const checks = selectChecks(cwd, ["crates/core/src/lib.rs"], "full");

		expect(checks.map((check) => check.id)).toEqual(["crates/core:check", "repository:precommit"]);
	});

	test("avoids PCB previews but still runs the repository gate during full validation", () => {
		const checks = selectChecks(cwd, ["hardware/pcb/generate.py"], "full");

		expect(checks.map((check) => check.id)).toEqual([
			"hardware/pcb:check-fast",
			"repository:precommit",
		]);
	});
});
