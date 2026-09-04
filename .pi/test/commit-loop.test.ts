import { afterEach, describe, expect, test } from "bun:test";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import commitLoop from "../extensions/commit-loop/index.js";
import { validateCommitPlan } from "../extensions/commit-loop/planner.js";

interface PlannedCommit {
	message: string;
	paths: string[];
}

const temporaryDirectories: string[] = [];
afterEach(async () => {
	await Promise.all(temporaryDirectories.splice(0).map((path) => rm(path, { recursive: true, force: true })));
});

async function run(command: string, args: string[], cwd: string) {
	const child = Bun.spawn([command, ...args], { cwd, stdout: "pipe", stderr: "pipe" });
	const [stdout, stderr, code] = await Promise.all([
		new Response(child.stdout).text(),
		new Response(child.stderr).text(),
		child.exited,
	]);
	return { stdout, stderr, code, killed: false };
}

async function createRepository(): Promise<string> {
	const repository = await mkdtemp(join(tmpdir(), "pi-commit-loop-test-"));
	temporaryDirectories.push(repository);
	await run("git", ["init", "-q", "-b", "main"], repository);
	await run("git", ["config", "user.name", "Pi Test"], repository);
	await run("git", ["config", "user.email", "pi@example.invalid"], repository);
	return repository;
}

function createHarness(
	repository: string,
	commits: PlannedCommit[],
	options: { choice?: string; editor?: string; cwd?: string } = {},
) {
	let commandHandler: ((args: string, ctx: any) => Promise<void>) | undefined;
	const reviews: string[] = [];
	const notices: string[] = [];
	const sentMessages: string[] = [];
	const editorCalls: unknown[][] = [];
	const pi = {
		registerCommand(name: string, registration: { handler: (args: string, ctx: any) => Promise<void> }) {
			if (name === "commit-loop") commandHandler = registration.handler;
		},
		on() {},
		events: { emit() {} },
		sendUserMessage(message: string) {
			sentMessages.push(message);
		},
		exec: (command: string, args: string[]) => run(command, args, repository),
	} as unknown as ExtensionAPI;
	commitLoop(pi);
	if (!commandHandler) throw new Error("/commit-loop was not registered");

	const context = {
		cwd: options.cwd ?? repository,
		hasUI: true,
		model: { provider: "faux", id: "planner" },
		modelRegistry: {
			hasConfiguredAuth: () => true,
			complete: async () => ({
				stopReason: "toolUse",
				content: [{
					type: "toolCall",
					id: "plan-1",
					name: "submit_commit_plan",
					arguments: { commits },
				}],
			}),
		},
		sessionManager: { getBranch: () => [] },
		waitForIdle: async () => {},
		ui: {
			editor: async (...args: unknown[]) => {
				editorCalls.push(args);
				return options.editor;
			},
			notify: (message: string) => notices.push(message),
			select: async (title: string) => {
				reviews.push(title);
				return options.choice ?? "Commit";
			},
			setStatus() {},
		},
	};
	return { commandHandler, context, editorCalls, notices, reviews, sentMessages };
}

describe("commit plan validation", () => {
	test("rejects paths repeated across tiny commits", () => {
		expect(() =>
			validateCommitPlan(
				{
					commits: [
						{ message: "Add hook", paths: ["hook.ts"] },
						{ message: "Test hook", paths: ["hook.ts"] },
					],
				},
				["hook.ts"],
			),
		).toThrow("same path more than once");
	});
});

describe("/commit-loop", () => {
	test("stages, reviews, validates, and commits each tiny step", async () => {
		const repository = await createRepository();
		await writeFile(join(repository, "README.md"), "before\n");
		await run("git", ["add", "README.md"], repository);
		await run("git", ["commit", "-qm", "Initial commit"], repository);
		await writeFile(join(repository, "README.md"), "before\n\nafter\n");
		await writeFile(join(repository, "NOTES.md"), "notes\n");
		await writeFile(join(repository, " leading.md"), "leading-space path\n");

		const harness = createHarness(repository, [
			{ message: "Update the readme", paths: ["README.md"] },
			{ message: "Add development notes", paths: ["NOTES.md"] },
			{ message: "Add unusual path fixture", paths: [" leading.md"] },
		]);
		await harness.commandHandler("document all steps", harness.context);

		const log = (await run("git", ["log", "-3", "--reverse", "--pretty=%s"], repository)).stdout.trim();
		expect(log.split("\n")).toEqual([
			"Update the readme",
			"Add development notes",
			"Add unusual path fixture",
		]);
		expect(harness.reviews).toHaveLength(3);
		expect(harness.reviews[0]).toContain("Staged commit 1/3");
		expect(harness.reviews[1]).toContain("Staged commit 2/3");
		expect(harness.reviews[2]).toContain("Staged commit 3/3");
		expect((await run("git", ["status", "--porcelain"], repository)).stdout).toBe("");
		expect(harness.notices.some((message) => message.includes("Commit loop complete"))).toBe(true);
	});

	test("validates each staged snapshot without later working-tree changes", async () => {
		const repository = await createRepository();
		await mkdir(join(repository, "crates/core/src"), { recursive: true });
		await writeFile(join(repository, "Cargo.toml"), '[workspace]\nmembers = ["crates/core"]\nresolver = "2"\n');
		await writeFile(join(repository, "crates/core/Cargo.toml"), '[package]\nname = "core"\nversion = "0.1.0"\nedition = "2024"\n');
		await writeFile(join(repository, "crates/core/src/lib.rs"), "pub fn existing() {}\n");
		await run("git", ["add", "."], repository);
		await run("git", ["commit", "-qm", "Initial crate"], repository);
		await writeFile(join(repository, "crates/core/src/lib.rs"), "mod generated;\npub use generated::value;\n");
		await writeFile(join(repository, "crates/core/src/generated.rs"), "pub fn value() {}\n");

		const harness = createHarness(repository, [
			{ message: "Expose generated value", paths: ["crates/core/src/lib.rs"] },
			{ message: "Implement generated value", paths: ["crates/core/src/generated.rs"] },
		]);
		await harness.commandHandler("split the crate update", harness.context);

		expect((await run("git", ["log", "-1", "--pretty=%s"], repository)).stdout.trim()).toBe("Initial crate");
		expect((await run("git", ["diff", "--cached", "--name-only"], repository)).stdout).toBe("");
		expect(harness.notices.some((message) => message.includes("Commit validation failed"))).toBe(true);
	});

	test("rejects whitespace errors in the staged patch", async () => {
		const repository = await createRepository();
		await writeFile(join(repository, "README.md"), "clean\n");
		await run("git", ["add", "README.md"], repository);
		await run("git", ["commit", "-qm", "Initial content"], repository);
		await writeFile(join(repository, "README.md"), "trailing whitespace   \n");

		const harness = createHarness(repository, [{ message: "Update readme", paths: ["README.md"] }]);
		await harness.commandHandler("update readme", harness.context);

		expect((await run("git", ["log", "-1", "--pretty=%s"], repository)).stdout.trim()).toBe("Initial content");
		expect((await run("git", ["diff", "--cached", "--name-only"], repository)).stdout).toBe("");
		expect(harness.notices.some((message) => message.includes("Staged patch check failed"))).toBe(true);
	});

	test("unstages rejected paths when launched from a nested directory", async () => {
		const repository = await createRepository();
		const nested = join(repository, "nested");
		await mkdir(nested);
		await writeFile(join(nested, "file.txt"), "before\n");
		await run("git", ["add", "nested/file.txt"], repository);
		await run("git", ["commit", "-qm", "Initial commit"], repository);
		await writeFile(join(nested, "file.txt"), "after\n");

		const harness = createHarness(
			repository,
			[{ message: "Update nested file", paths: ["nested/file.txt"] }],
			{ choice: "Needs changes", editor: "Keep the original first line.", cwd: nested },
		);
		await harness.commandHandler("update nested file", harness.context);

		expect((await run("git", ["diff", "--cached", "--name-only"], repository)).stdout).toBe("");
		expect(harness.editorCalls).toEqual([["Describe the changes needed in the patch or commit message"]]);
		expect(harness.sentMessages[0]).toContain("Keep the original first line.");
	});
});
