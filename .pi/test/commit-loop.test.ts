import { afterEach, describe, expect, test } from "bun:test";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import commitLoop from "../extensions/commit-loop/index.js";
import { validateCommitPlan } from "../extensions/commit-loop/planner.js";

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
		const repository = await mkdtemp(join(tmpdir(), "pi-commit-loop-test-"));
		temporaryDirectories.push(repository);
		await run("git", ["init", "-q", "-b", "main"], repository);
		await run("git", ["config", "user.name", "Pi Test"], repository);
		await run("git", ["config", "user.email", "pi@example.invalid"], repository);
		await writeFile(join(repository, "README.md"), "before\n");
		await run("git", ["add", "README.md"], repository);
		await run("git", ["commit", "-qm", "Initial commit"], repository);
		await writeFile(join(repository, "README.md"), "before\n\nafter\n");
		await writeFile(join(repository, "NOTES.md"), "notes\n");

		let commandHandler: ((args: string, ctx: any) => Promise<void>) | undefined;
		const reviews: string[] = [];
		const notices: string[] = [];
		const pi = {
			registerCommand(name: string, options: { handler: (args: string, ctx: any) => Promise<void> }) {
				if (name === "commit-loop") commandHandler = options.handler;
			},
			on() {},
			events: { emit() {} },
			sendUserMessage() {},
			exec: (command: string, args: string[]) => run(command, args, repository),
		} as unknown as ExtensionAPI;
		commitLoop(pi);
		if (!commandHandler) throw new Error("/commit-loop was not registered");

		await commandHandler("document both steps", {
			cwd: repository,
			hasUI: true,
			model: { provider: "faux", id: "planner" },
			modelRegistry: {
				hasConfiguredAuth: () => true,
				complete: async () => ({
					stopReason: "toolUse",
					content: [
						{
							type: "toolCall",
							id: "plan-1",
							name: "submit_commit_plan",
							arguments: {
								commits: [
									{ message: "Update the readme", paths: ["README.md"] },
									{ message: "Add development notes", paths: ["NOTES.md"] },
								],
							},
						},
					],
				}),
			},
			sessionManager: { getBranch: () => [] },
			waitForIdle: async () => {},
			ui: {
				editor: async () => undefined,
				notify: (message: string) => notices.push(message),
				select: async (title: string) => {
					reviews.push(title);
					return "Commit";
				},
				setStatus() {},
			},
		});

		const log = (await run("git", ["log", "-2", "--reverse", "--pretty=%s"], repository)).stdout.trim();
		expect(log.split("\n")).toEqual(["Update the readme", "Add development notes"]);
		expect(reviews).toHaveLength(2);
		expect(reviews[0]).toContain("Staged commit 1/2");
		expect(reviews[1]).toContain("Staged commit 2/2");
		expect((await run("git", ["status", "--porcelain"], repository)).stdout).toBe("");
		expect(notices.some((message) => message.includes("Commit loop complete"))).toBe(true);
	});
});
