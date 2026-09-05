import { describe, expect, test } from "bun:test";
import { suspiciousPatchLines } from "../extensions/pr-workflow/git.js";
import { validatePrPlan, type PrPlan } from "../extensions/pr-workflow/planner.js";

function plan(overrides: Partial<PrPlan> = {}): PrPlan {
	return {
		branch: "feat/pi-feedback-loop",
		title: "Add a modular Pi feedback loop",
		body: "## Summary\n\nAdd feedback hooks.\n\n## Validation\n\n- Bun checks",
		commits: [
			{ message: "Simplify Pi commit hooks", paths: [".pi/extensions/commit-loop/index.ts"] },
		],
		...overrides,
	};
}

describe("PR plan validation", () => {
	test("allows the plan to omit unrelated dirty files", () => {
		expect(
			validatePrPlan(plan(), [
				".pi/extensions/commit-loop/index.ts",
				"crates/chess/src/lib.rs",
			]),
		).toEqual([".pi/extensions/commit-loop/index.ts"]);
	});

	test("rejects duplicate paths across sequential commits", () => {
		expect(() =>
			validatePrPlan(
				plan({
					commits: [
						{ message: "Add hooks", paths: [".pi/package.json"] },
						{ message: "Test hooks", paths: [".pi/package.json"] },
					],
				}),
				[".pi/package.json"],
			),
		).toThrow("same path more than once");
	});

	test("rejects non-semantic branch names", () => {
		expect(() =>
			validatePrPlan(plan({ branch: "my changes" }), [".pi/extensions/commit-loop/index.ts"]),
		).toThrow("invalid semantic branch name");
	});

	test("rejects incomplete PR body structure", () => {
		expect(() =>
			validatePrPlan(plan({ body: "Just some prose" }), [".pi/extensions/commit-loop/index.ts"]),
		).toThrow("## Summary and ## Validation");
	});
});

describe("secret scanning", () => {
	test("flags likely added credentials but ignores ordinary additions", () => {
		const findings = suspiciousPatchLines(
			[
				"+const enabled = true;",
				'+api_key = "definitely-not-a-real-secret-value"',
				'+AWS_SECRET_ACCESS_KEY = "quoted-secret-value"',
				"+STRIPE_SECRET_KEY = 'another-secret-value'",
				'+  "client_secret": "structured-secret-value"',
				"+  password: unquoted-secret-value",
			].join("\n"),
		);
		expect(findings).toEqual([
			'+api_key = "definitely-not-a-real-secret-value"',
			'+AWS_SECRET_ACCESS_KEY = "quoted-secret-value"',
			"+STRIPE_SECRET_KEY = 'another-secret-value'",
			'+  "client_secret": "structured-secret-value"',
			"+  password: unquoted-secret-value",
		]);
		expect(suspiciousPatchLines("+client-secret: hyphenated-secret-value")).toEqual([
			"+client-secret: hyphenated-secret-value",
		]);
		expect(suspiciousPatchLines("+-----BEGIN ENCRYPTED PRIVATE KEY-----")).toEqual([
			"+-----BEGIN ENCRYPTED PRIVATE KEY-----",
		]);
		expect(suspiciousPatchLines("+  - password: sequence-secret-value")).toEqual([
			"+  - password: sequence-secret-value",
		]);
		expect(suspiciousPatchLines(
			"+API_KEY=super-secret-value\n+AWS_SECRET_ACCESS_KEY=abcdefghijklmnop # production\n+DATABASE_PASSWORD: secret-value\n+MODE=development",
		)).toEqual([
			"+API_KEY=super-secret-value",
			"+AWS_SECRET_ACCESS_KEY=abcdefghijklmnop # production",
			"+DATABASE_PASSWORD: secret-value",
		]);
		expect(suspiciousPatchLines(
			"+credential=github_pat_11AA22BB33CC44DD55EE66FF77GG88HH",
		)).toEqual(["+credential=github_pat_11AA22BB33CC44DD55EE66FF77GG88HH"]);
	});
});
