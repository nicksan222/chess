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

	test("parses changed package justfiles alongside Rust checks", () => {
		const checks = selectChecks(cwd, ["crates/core/justfile"], "fast");

		expect(checks.map((check) => check.id)).toEqual([
			"crates/core:cargo-check",
			"crates/core/justfile:just-format",
		]);
		expect(checks[1]?.args).toEqual([
			"--unstable",
			"--justfile",
			"/repo/crates/core/justfile",
			"--fmt",
			"--check",
		]);
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

	test("parses selected Yocto metadata through the container image check", () => {
		for (const level of ["fast", "full"] as const) {
			const checks = selectChecks(cwd, ["apps/firmware/yocto/kas/firmware.yml"], level);
			expect(checks[0]).toEqual({
				id: "apps/firmware:image-check",
				command: "just",
				args: ["--justfile", "/repo/apps/firmware/justfile", "image-check"],
				timeoutMs: 15 * 60 * 1000,
			});
		}
	});

	test("retains checks for other packages alongside Yocto metadata", () => {
		const checks = selectChecks(
			cwd,
			["apps/firmware/yocto/kas/firmware.yml", "crates/core/src/lib.rs"],
			"fast",
		);

		expect(checks.map((check) => check.id)).toEqual([
			"apps/firmware:image-check",
			"crates/core:cargo-check",
		]);
	});

	test("retains firmware code checks in mixed Yocto batches", () => {
		const checks = selectChecks(
			cwd,
			["apps/firmware/src/main.rs", "apps/firmware/yocto/kas/firmware.yml"],
			"fast",
		);

		expect(checks.map((check) => check.id)).toEqual([
			"apps/firmware:quality",
			"apps/firmware:image-check",
		]);
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

	test("checks harness shell syntax alongside Pi configuration", () => {
		for (const path of [".devcontainer/post-create.sh", ".github/scripts/with-devcontainer.sh"]) {
			const checks = selectChecks(cwd, [path], "fast");
			expect(checks.map((check) => check.id)).toEqual([
				".pi:check",
				`${path}:bash-syntax`,
			]);
		}
	});

	test("checks the version-controlled Git hook as Bash", () => {
		const checks = selectChecks(cwd, [".githooks/pre-commit"], "fast");

		expect(checks.map((check) => check.id)).toEqual([
			".githooks/pre-commit:bash-syntax",
			"repository:diff-check",
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
		const checks = selectChecks(cwd, ["README.md"], "fast");

		expect(checks.map((check) => check.id)).toEqual(["repository:diff-check"]);
		expect(checks[0]?.command).toBe("git");
		expect(checks[0]?.args).toEqual(["-C", cwd, "diff", "--check", "--", "README.md"]);
	});

	test("checks committed unscoped changes from their base revision", () => {
		const checks = selectChecks(cwd, ["README.md"], "fast", "before-turn");

		expect(checks[0]?.args).toEqual(["-C", cwd, "diff", "--check", "before-turn", "--", "README.md"]);
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
