import { describe, expect, test } from "bun:test";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import autoValidation from "../extensions/auto-validation/index.js";

const REPOSITORY = "/tmp/example-repository";

describe("automatic validation", () => {
	test("runs from the repository recorded by change tracking", async () => {
		const eventHandlers = new Map<string, (payload: unknown) => void>();
		const hooks = new Map<string, (...args: any[]) => unknown>();
		const executions: string[][] = [];
		const pi = {
			events: {
				on(name: string, handler: (payload: unknown) => void) {
					eventHandlers.set(name, handler);
				},
				emit() {},
			},
			on(name: string, handler: (...args: any[]) => unknown) {
				hooks.set(name, handler);
			},
			exec: async (command: string, args: string[]) => {
				executions.push([command, ...args]);
				return { stdout: "", stderr: "", code: 0, killed: false };
			},
			sendMessage() {},
		} as unknown as ExtensionAPI;
		autoValidation(pi);

		eventHandlers.get("feedback:files-changed")?.({ cwd: REPOSITORY, paths: ["README.md"] });
		await hooks.get("agent_end")?.({}, { cwd: `${REPOSITORY}/nested`, signal: undefined, ui: { notify() {} } });

		expect(executions).toEqual([["git", "-C", REPOSITORY, "diff", "--check"]]);
	});
});
