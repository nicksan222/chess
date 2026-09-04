import { describe, expect, test } from "bun:test";
import { pathsFromNameStatus } from "../feedback/git-paths.js";

describe("Git path parsing", () => {
	test("returns both sides of renames and copies", () => {
		expect(pathsFromNameStatus("M\0changed.ts\0R100\0old.ts\0new.ts\0C75\0source.ts\0copy.ts\0")).toEqual([
			"changed.ts",
			"copy.ts",
			"new.ts",
			"old.ts",
			"source.ts",
		]);
	});
});
