import { afterEach, describe, expect, test } from "bun:test";
import { mkdir, mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import changeTracker, { FILES_CHANGED_EVENT } from "../extensions/change-tracker/index.js";

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

describe("change tracker", () => {
	test("reports files edited and committed during one turn", async () => {
		const repository = await mkdtemp(join(tmpdir(), "pi-change-tracker-test-"));
		temporaryDirectories.push(repository);
		const nested = join(repository, "nested");
		await mkdir(nested);
		await run("git", ["init", "-q", "-b", "main"], repository);
		await run("git", ["config", "user.name", "Pi Test"], repository);
		await run("git", ["config", "user.email", "pi@example.invalid"], repository);
		await writeFile(join(nested, "file.txt"), "before\n");
		await run("git", ["add", "."], repository);
		await run("git", ["commit", "-qm", "Initial commit"], repository);
		const initialHead = (await run("git", ["rev-parse", "HEAD"], repository)).stdout.trim();

		const hooks = new Map<string, (...args: any[]) => unknown>();
		const emitted: Array<{ name: string; payload: any }> = [];
		const pi = {
			on(name: string, handler: (...args: any[]) => unknown) {
				hooks.set(name, handler);
			},
			events: {
				emit(name: string, payload: any) {
					emitted.push({ name, payload });
				},
			},
			exec: (command: string, args: string[]) => run(command, args, repository),
		} as unknown as ExtensionAPI;
		changeTracker(pi);
		const context = { cwd: nested };

		await hooks.get("turn_start")?.({}, context);
		await hooks.get("tool_call")?.({ toolName: "edit", input: { path: "file.txt" } }, context);
		await writeFile(join(nested, "file.txt"), "after\n");
		await run("git", ["add", "."], repository);
		await run("git", ["commit", "-qm", "Commit inside turn"], repository);
		await hooks.get("turn_end")?.({}, context);

		expect(emitted).toHaveLength(1);
		expect(emitted[0]?.name).toBe(FILES_CHANGED_EVENT);
		expect(emitted[0]?.payload).toMatchObject({
			cwd: repository,
			paths: ["nested/file.txt"],
			baseRevision: initialHead,
			explicitPaths: ["nested/file.txt"],
			snapshotPaths: [],
			attribution: "tool",
		});
	});
});
