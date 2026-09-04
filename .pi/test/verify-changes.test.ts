import { describe, expect, test } from "bun:test";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { verify } from "../extensions/verify-changes/index.js";

const REPOSITORY = "/tmp/example-repository";

describe("verify_changes", () => {
	test("resolves nested working directories to the repository root", async () => {
		const executions: string[][] = [];
		const pi = {
			events: { emit() {} },
			exec: async (command: string, args: string[]) => {
				executions.push([command, ...args]);
				if (args.includes("--show-toplevel")) {
					return { stdout: `${REPOSITORY}\n`, stderr: "", code: 0, killed: false };
				}
				if (args.includes("--name-status")) {
					return { stdout: "M\0README.md\0", stderr: "", code: 0, killed: false };
				}
				return { stdout: "", stderr: "", code: 0, killed: false };
			},
		} as unknown as ExtensionAPI;

		const result = await verify(pi, `${REPOSITORY}/nested`, "fast", undefined);

		expect(result.paths).toEqual(["README.md"]);
		expect(executions.at(-1)).toEqual(["git", "-C", REPOSITORY, "diff", "--check"]);
	});
});
