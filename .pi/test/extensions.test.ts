import { describe, expect, test } from "bun:test";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import commitLoop from "../extensions/commit-loop/index.js";
import prWorkflow from "../extensions/pr-workflow/index.js";

describe("project extensions", () => {
	test("register only the commit and pull-request commands", () => {
		const commands: string[] = [];
		const pi = {
			registerCommand(name: string) {
				commands.push(name);
			},
			on() {},
		} as unknown as ExtensionAPI;

		commitLoop(pi);
		prWorkflow(pi);

		expect(commands.sort()).toEqual(["commit-loop", "pr"]);
	});
});
