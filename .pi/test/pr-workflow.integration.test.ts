import { afterEach, describe, expect, test } from "bun:test";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import prWorkflow from "../extensions/pr-workflow/index.js";

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

describe("standalone /pr workflow", () => {
	test("creates a semantic branch and local validated commits without a remote", async () => {
		const repository = await mkdtemp(join(tmpdir(), "pi-pr-workflow-test-"));
		temporaryDirectories.push(repository);
		await run("git", ["init", "-q", "-b", "main"], repository);
		await run("git", ["config", "user.name", "Pi Test"], repository);
		await run("git", ["config", "user.email", "pi@example.invalid"], repository);
		await writeFile(join(repository, "README.md"), "before\n");
		await run("git", ["add", "README.md"], repository);
		await run("git", ["commit", "-qm", "Initial commit"], repository);
		await writeFile(join(repository, "README.md"), "before\n\nafter\n");

		let commandHandler: ((args: string, ctx: any) => Promise<void>) | undefined;
		const notices: Array<{ message: string; level: string }> = [];
		const pi = {
			registerCommand(name: string, options: { handler: (args: string, ctx: any) => Promise<void> }) {
				if (name === "pr") commandHandler = options.handler;
			},
			async exec(command: string, args: string[]) {
				if (command === "gh") return { stdout: "", stderr: "not authenticated", code: 1, killed: false };
				if (command === "just") return { stdout: "validation passed", stderr: "", code: 0, killed: false };
				return run(command, args, repository);
			},
			events: { emit() {} },
			setSessionName() {},
		} as unknown as ExtensionAPI;
		prWorkflow(pi);
		if (!commandHandler) throw new Error("/pr was not registered");

		await commandHandler("document the change", {
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
							name: "submit_pr_plan",
							arguments: {
								branch: "docs/standalone-pr-workflow",
								title: "Document the standalone PR workflow",
								body: "## Summary\n\nDocument the change.\n\n## Validation\n\n- Repository checks",
								commits: [{ message: "Document the PR workflow", paths: ["README.md"] }],
							},
						},
					],
				}),
			},
			sessionManager: { getBranch: () => [] },
			waitForIdle: async () => {},
			ui: {
				confirm: async () => true,
				notify: (message: string, level: string) => notices.push({ message, level }),
				setStatus() {},
			},
		});

		const branch = (await run("git", ["branch", "--show-current"], repository)).stdout.trim();
		const subject = (await run("git", ["log", "-1", "--pretty=%s"], repository)).stdout.trim();
		const status = (await run("git", ["status", "--porcelain"], repository)).stdout.trim();
		expect(branch).toBe("docs/standalone-pr-workflow");
		expect(subject).toBe("Document the PR workflow");
		expect(status).toBe("");
		expect(await readFile(join(repository, "README.md"), "utf8")).toContain("after");
		expect(notices.some(({ message, level }) => level === "warning" && message.includes("Created and validated local commits"))).toBe(true);
	});
});
