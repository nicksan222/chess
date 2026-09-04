import { describe, expect, test } from "bun:test";
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import YAML from "yaml";

const repository = resolve(import.meta.dir, "../..");

async function text(path: string): Promise<string> {
	return readFile(resolve(repository, path), "utf8");
}

describe("Pi harness configuration", () => {
	test("keeps project JSON parseable", async () => {
		for (const path of [".devcontainer/devcontainer.json", ".pi/package.json", ".pi/tsconfig.json"]) {
			const document = await text(path);
			expect(() => JSON.parse(document)).not.toThrow();
		}
	});

	test("persists Pi state and automatic worktrees", async () => {
		const config = JSON.parse(await text(".devcontainer/devcontainer.json"));
		expect(config.mounts).toContain("source=chess-pi-agent,target=/home/vscode/.pi/agent,type=volume");
		expect(config.mounts).toContain("source=chess-pi-worktrees,target=/home/vscode/.worktrees,type=volume");
	});

	test("keeps every GitHub workflow and action parseable", async () => {
		const paths = [...new Bun.Glob(".github/**/*.{yml,yaml}").scanSync({ cwd: repository })];
		expect(paths.length).toBeGreaterThan(0);
		for (const path of paths) {
			const workflow = await text(path);
			expect(() => YAML.parse(workflow)).not.toThrow();
		}
	});

	test("keeps every harness shell script parseable", () => {
		const paths = [
			".githooks/pre-commit",
			...[".github", ".devcontainer"].flatMap((directory) =>
				[...new Bun.Glob(`${directory}/**/*.sh`).scanSync({ cwd: repository })]
			),
		];
		expect(paths.length).toBeGreaterThan(0);
		for (const path of paths) {
			expect(Bun.spawnSync(["bash", "-n", resolve(repository, path)]).exitCode).toBe(0);
		}
	});

	test("keeps the CI workflow parseable and requires Bun validation", async () => {
		const workflow = await text(".github/workflows/ci.yml");
		expect(() => YAML.parse(workflow)).not.toThrow();
		expect(workflow).toContain("oven-sh/setup-bun@v2");
		expect(workflow).toContain("bun install --cwd .pi --frozen-lockfile");
		expect(workflow).toContain("bun run --cwd .pi check");
		expect(workflow).toContain("pi-harness");
	});

	test("checks the locked Pi project when the devcontainer is created", async () => {
		const script = await text(".devcontainer/post-create.sh");
		expect(script).toContain('"${HOME}/.pi/agent" "${HOME}/.worktrees"');
		expect(script).toContain("bun install --cwd .pi --frozen-lockfile");
		expect(script).toContain("bun run --cwd .pi check");
	});
});
