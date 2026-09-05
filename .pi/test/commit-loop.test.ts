import { afterEach, describe, expect, test } from "bun:test";
import { chmod, mkdir, mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
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
	options: {
		beforeChoice?: () => Promise<void>;
		choice?: string;
		cwd?: string;
		editor?: string;
	} = {},
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
				await options.beforeChoice?.();
				return options.choice ?? "Commit";
			},
			setStatus() {},
		},
	};
	return { commandHandler, context, editorCalls, notices, reviews, sentMessages };
}

describe("commit plan validation", () => {
	test("rejects paths repeated across tiny commits", () => {
		expect(() => validateCommitPlan({ commits: [
			{ message: "Add hook", paths: ["hook.ts"] },
			{ message: "Test hook", paths: ["hook.ts"] },
		] }, ["hook.ts"])).toThrow("same path more than once");
	});
});

describe("/commit-loop", () => {
	test("runs the Git pre-commit hook for every generated commit", async () => {
		const repository = await createRepository();
		await writeFile(join(repository, "README.md"), "before\n");
		await run("git", ["add", "README.md"], repository);
		await run("git", ["commit", "-qm", "Initial commit"], repository);
		await writeFile(join(repository, "README.md"), "before\n\nafter\n");
		await writeFile(join(repository, "NOTES.md"), "notes\n");
		const hook = join(repository, ".git/hooks/pre-commit");
		await writeFile(hook, "#!/bin/sh\nprintf 'run\\n' >> \"$(git rev-parse --git-dir)/hook-runs\"\n");
		await chmod(hook, 0o755);

		const harness = createHarness(repository, [
			{ message: "Update the readme", paths: ["README.md"] },
			{ message: "Add development notes", paths: ["NOTES.md"] },
		]);
		await harness.commandHandler("document all steps", harness.context);

		expect((await readFile(join(repository, ".git/hook-runs"), "utf8")).split("\n").filter(Boolean)).toHaveLength(2);
		expect((await run("git", ["log", "-2", "--reverse", "--pretty=%s"], repository)).stdout.trim().split("\n")).toEqual([
			"Update the readme",
			"Add development notes",
		]);
		expect(harness.reviews).toHaveLength(2);
		expect((await run("git", ["status", "--porcelain"], repository)).stdout).toBe("");
	});

	test("stops when the Git pre-commit hook rejects a commit", async () => {
		const repository = await createRepository();
		await writeFile(join(repository, "README.md"), "before\n");
		await run("git", ["add", "README.md"], repository);
		await run("git", ["commit", "-qm", "Initial commit"], repository);
		await writeFile(join(repository, "README.md"), "after\n");
		const hook = join(repository, ".git/hooks/pre-commit");
		await writeFile(hook, "#!/bin/sh\nexit 1\n");
		await chmod(hook, 0o755);

		const harness = createHarness(repository, [{ message: "Update readme", paths: ["README.md"] }]);
		await harness.commandHandler("update documentation", harness.context);

		expect((await run("git", ["log", "-1", "--pretty=%s"], repository)).stdout.trim()).toBe("Initial commit");
		expect(harness.notices.some((message) => message.includes("git commit"))).toBe(true);
		expect((await run("git", ["diff", "--cached", "--name-only"], repository)).stdout.trim()).toBe("README.md");
	});

	test("rejects index drift after review", async () => {
		const repository = await createRepository();
		await writeFile(join(repository, "README.md"), "before\n");
		await writeFile(join(repository, "EXTRA.md"), "before\n");
		await run("git", ["add", "."], repository);
		await run("git", ["commit", "-qm", "Initial commit"], repository);
		await writeFile(join(repository, "README.md"), "after\n");
		const harness = createHarness(repository, [{ message: "Update readme", paths: ["README.md"] }], {
			beforeChoice: async () => {
				await writeFile(join(repository, "EXTRA.md"), "late staged change\n");
				await run("git", ["add", "EXTRA.md"], repository);
			},
		});

		await harness.commandHandler("update documentation", harness.context);

		expect((await run("git", ["log", "-1", "--pretty=%s"], repository)).stdout.trim()).toBe("Initial commit");
		expect(harness.notices).toContain("The staged index changed during review; the proposed commit was unstaged.");
		expect((await run("git", ["diff", "--cached", "--name-only"], repository)).stdout.trim()).toBe("EXTRA.md");
	});

	test("unstages rejected paths when launched from a nested directory", async () => {
		const repository = await createRepository();
		const nested = join(repository, "nested");
		await mkdir(nested);
		await writeFile(join(nested, "file.txt"), "before\n");
		await run("git", ["add", "nested/file.txt"], repository);
		await run("git", ["commit", "-qm", "Initial commit"], repository);
		await writeFile(join(nested, "file.txt"), "after\n");

		const harness = createHarness(repository, [{ message: "Update nested file", paths: ["nested/file.txt"] }], {
			choice: "Needs changes",
			cwd: nested,
			editor: "Keep the original first line.",
		});
		await harness.commandHandler("update nested file", harness.context);

		expect((await run("git", ["diff", "--cached", "--name-only"], repository)).stdout).toBe("");
		expect(harness.editorCalls).toEqual([["Describe the changes needed in the patch or commit message"]]);
		expect(harness.sentMessages[0]).toContain("Keep the original first line.");
	});
});
