import { describe, expect, test } from "bun:test";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import autoValidation from "../extensions/auto-validation/index.js";
import autoWorktree from "../extensions/auto-worktree/index.js";
import commitLoop from "../extensions/commit-loop/index.js";
import changeTracker, { attributedChanges } from "../extensions/change-tracker/index.js";
import prWorkflow from "../extensions/pr-workflow/index.js";
import validationStatus from "../extensions/validation-status/index.js";
import verifyChanges from "../extensions/verify-changes/index.js";

function registrationHarness() {
	const commands: string[] = [];
	const tools: string[] = [];
	const hooks: string[] = [];
	const busEvents: string[] = [];
	const hookHandlers = new Map<string, (...args: any[]) => unknown>();
	const sentUserMessages: string[] = [];
	const pi = {
		events: {
			on(name: string) {
				busEvents.push(name);
			},
			emit() {},
		},
		on(name: string, handler: (...args: any[]) => unknown) {
			hooks.push(name);
			hookHandlers.set(name, handler);
		},
		registerCommand(name: string) {
			commands.push(name);
		},
		registerTool(tool: { name: string }) {
			tools.push(tool.name);
		},
		sendUserMessage(message: string) {
			sentUserMessages.push(message);
		},
	} as unknown as ExtensionAPI;
	return { pi, commands, tools, hooks, busEvents, hookHandlers, sentUserMessages };
}

describe("project extensions", () => {
	test("load independently and register focused capabilities", () => {
		const harness = registrationHarness();
		for (const extension of [
			autoValidation,
			autoWorktree,
			commitLoop,
			changeTracker,
			prWorkflow,
			validationStatus,
			verifyChanges,
		]) {
			extension(harness.pi);
		}

		expect(harness.tools).toEqual(["verify_changes"]);
		expect(harness.commands.sort()).toEqual([
			"auto-worktree-bootstrap",
			"commit-loop",
			"pr",
			"validation-clear",
			"verify",
		]);
		expect(harness.hooks).toContain("turn_start");
		expect(harness.hooks).toContain("turn_end");
		expect(harness.hooks).toContain("agent_end");
		expect(harness.busEvents).toContain("feedback:files-changed");
		expect(harness.busEvents).toContain("feedback:validation-result");
	});

	test("keeps shell-mutated paths when explicit tool paths also exist", () => {
		expect(
			attributedChanges(
				["explicit.ts", "generated.ts"],
				new Set(["explicit.ts"]),
			),
		).toEqual({
			paths: ["explicit.ts", "generated.ts"],
			explicitPaths: ["explicit.ts"],
			snapshotPaths: ["generated.ts"],
			attribution: "mixed",
		});
	});

	test("queues automatic worktree setup once on process startup", async () => {
		const previousActive = process.env.PI_AUTO_WORKTREE_ACTIVE;
		const previousDisabled = process.env.PI_AUTO_WORKTREE_DISABLE;
		delete process.env.PI_AUTO_WORKTREE_ACTIVE;
		delete process.env.PI_AUTO_WORKTREE_DISABLE;
		try {
			const harness = registrationHarness();
			autoWorktree(harness.pi);
			const sessionStart = harness.hookHandlers.get("session_start");
			expect(sessionStart).toBeDefined();
			sessionStart?.(
				{ reason: "startup" },
				{ sessionManager: { getSessionId: () => "session-123" }, ui: { notify() {} } },
			);
			await Promise.resolve();

			expect(harness.sentUserMessages).toEqual(["/auto-worktree-bootstrap"]);
			expect(String(process.env.PI_AUTO_WORKTREE_ACTIVE)).toBe("session-123");
		} finally {
			if (previousActive === undefined) delete process.env.PI_AUTO_WORKTREE_ACTIVE;
			else process.env.PI_AUTO_WORKTREE_ACTIVE = previousActive;
			if (previousDisabled === undefined) delete process.env.PI_AUTO_WORKTREE_DISABLE;
			else process.env.PI_AUTO_WORKTREE_DISABLE = previousDisabled;
		}
	});
});
