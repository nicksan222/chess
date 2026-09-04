import { afterEach, describe, expect, test } from "bun:test";
import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import prWorkflow from "../extensions/pr-workflow/index.js";
import type { PrPlan } from "../extensions/pr-workflow/planner.js";

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
	const repository = await mkdtemp(join(tmpdir(), "pi-pr-workflow-test-"));
	temporaryDirectories.push(repository);
	await run("git", ["init", "-q", "-b", "main"], repository);
	await run("git", ["config", "user.name", "Pi Test"], repository);
	await run("git", ["config", "user.email", "pi@example.invalid"], repository);
	await writeFile(join(repository, "README.md"), "before\n");
	await run("git", ["add", "README.md"], repository);
	await run("git", ["commit", "-qm", "Initial commit"], repository);
	return repository;
}

function createHarness(repository: string, plan: PrPlan) {
	let commandHandler: ((args: string, ctx: any) => Promise<void>) | undefined;
	let planningCalls = 0;
	const notices: Array<{ message: string; level: string }> = [];
	const confirmations: string[] = [];
	const pi = {
		registerCommand(name: string, registration: { handler: (args: string, ctx: any) => Promise<void> }) {
			if (name === "pr") commandHandler = registration.handler;
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

	const context = {
		cwd: repository,
		hasUI: true,
		model: { provider: "faux", id: "planner" },
		modelRegistry: {
			hasConfiguredAuth: () => true,
			complete: async () => {
				planningCalls += 1;
				return {
					stopReason: "toolUse",
					content: [{
						type: "toolCall",
						id: "plan-1",
						name: "submit_pr_plan",
						arguments: plan,
					}],
				};
			},
		},
		sessionManager: { getBranch: () => [] },
		waitForIdle: async () => {},
		ui: {
			confirm: async (_title: string, details: string) => {
				confirmations.push(details);
				return true;
			},
			notify: (message: string, level: string) => notices.push({ message, level }),
			setStatus() {},
		},
	};
	return { commandHandler, confirmations, context, notices, planningCalls: () => planningCalls };
}

const DOCUMENTATION_PLAN: PrPlan = {
	branch: "docs/standalone-pr-workflow",
	title: "Document the standalone PR workflow",
	body: "## Summary\n\nDocument the change.\n\n## Validation\n\n- Repository checks",
	commits: [{ message: "Document the PR workflow", paths: ["README.md"] }],
};

describe("standalone /pr workflow", () => {
	test("creates a semantic branch and local validated commits without a remote", async () => {
		const repository = await createRepository();
		await writeFile(join(repository, "README.md"), "before\n\nafter\n");
		const harness = createHarness(repository, DOCUMENTATION_PLAN);

		await harness.commandHandler("document the change", harness.context);

		expect((await run("git", ["branch", "--show-current"], repository)).stdout.trim()).toBe("docs/standalone-pr-workflow");
		expect((await run("git", ["log", "-1", "--pretty=%s"], repository)).stdout.trim()).toBe("Document the PR workflow");
		expect((await run("git", ["status", "--porcelain"], repository)).stdout.trim()).toBe("");
		expect(await readFile(join(repository, "README.md"), "utf8")).toContain("after");
		expect(harness.notices.some(({ message, level }) => level === "warning" && message.includes("Created and validated local commits"))).toBe(true);
	});

	test("shows and publishes existing branch commits without recreating them", async () => {
		const repository = await createRepository();
		const remote = await mkdtemp(join(tmpdir(), "pi-pr-workflow-remote-"));
		temporaryDirectories.push(remote);
		await run("git", ["init", "--bare", "-q"], remote);
		await run("git", ["remote", "add", "origin", remote], repository);
		await run("git", ["push", "-q", "-u", "origin", "main"], repository);
		await run("git", ["switch", "-q", "-c", "pi/session"], repository);
		await writeFile(join(repository, "README.md"), "committed change\n");
		await run("git", ["add", "README.md"], repository);
		await run("git", ["commit", "-qm", "Document existing workflow"], repository);
		const plan: PrPlan = {
			...DOCUMENTATION_PLAN,
			branch: "docs/existing-workflow",
			commits: [],
		};
		const harness = createHarness(repository, plan);

		await harness.commandHandler("publish the existing commit", harness.context);

		expect(harness.confirmations[0]).toContain("Existing commits:\n");
		expect(harness.confirmations[0]).toContain("Document existing workflow");
		expect(harness.confirmations[0]).toContain("Planned commits:\n(none; publish existing commits only)");
		expect((await run("git", ["branch", "--show-current"], repository)).stdout.trim()).toBe("docs/existing-workflow");
		expect((await run("git", ["log", "-1", "--pretty=%s"], repository)).stdout.trim()).toBe("Document existing workflow");
	});

	test("blocks secrets in existing commits before invoking the planning model", async () => {
		const repository = await createRepository();
		const remote = await mkdtemp(join(tmpdir(), "pi-pr-workflow-secret-remote-"));
		temporaryDirectories.push(remote);
		await run("git", ["init", "--bare", "-q"], remote);
		await run("git", ["remote", "add", "origin", remote], repository);
		await run("git", ["push", "-q", "-u", "origin", "main"], repository);
		await run("git", ["switch", "-q", "-c", "pi/session"], repository);
		await writeFile(join(repository, "credentials.env"), 'api_key = "committed-secret-value"\n');
		await run("git", ["add", "credentials.env"], repository);
		await run("git", ["commit", "-qm", "Add accidental credential"], repository);
		const harness = createHarness(repository, { ...DOCUMENTATION_PLAN, commits: [] });

		await harness.commandHandler("prepare the pull request", harness.context);

		expect(harness.planningCalls()).toBe(0);
		expect(harness.notices.some(({ message }) => message.includes("Potential secret material"))).toBe(true);
	});

	test("blocks suspicious additions before invoking the planning model", async () => {
		const repository = await createRepository();
		await writeFile(join(repository, "credentials.env"), 'api_key = "super-secret-value"\n');
		const harness = createHarness(repository, DOCUMENTATION_PLAN);

		await harness.commandHandler("prepare the pull request", harness.context);

		expect(harness.planningCalls()).toBe(0);
		expect(harness.notices.some(({ message }) => message.includes("Potential secret material"))).toBe(true);
	});
});
