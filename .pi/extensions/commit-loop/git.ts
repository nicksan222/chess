import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { createValidationWorktree } from "../../feedback/snapshot.js";

const MAX_PATCH_BYTES = 256 * 1024;

function splitNull(value: string): string[] {
	return value.split("\0").filter((item) => item.length > 0);
}

function combinedOutput(result: { stdout: string; stderr: string }): string {
	return [result.stdout, result.stderr].filter(Boolean).join("\n").trim();
}

export async function git(pi: ExtensionAPI, cwd: string, args: string[], allowFailure = false) {
	const result = await pi.exec("git", ["-C", cwd, ...args]);
	if (!allowFailure && result.code !== 0) {
		throw new Error(`git ${args.join(" ")} failed: ${combinedOutput(result) || `exit ${result.code}`}`);
	}
	return result;
}

export async function dirtyPaths(pi: ExtensionAPI, cwd: string): Promise<string[]> {
	const tracked = await git(pi, cwd, ["diff", "--name-only", "-z", "HEAD", "--"]);
	const untracked = await git(pi, cwd, ["ls-files", "--others", "--exclude-standard", "-z", "--"]);
	return [...new Set([...splitNull(tracked.stdout), ...splitNull(untracked.stdout)])].sort();
}

export async function completePatch(
	pi: ExtensionAPI,
	cwd: string,
	paths: readonly string[],
): Promise<string> {
	const tracked = await git(pi, cwd, ["diff", "--no-ext-diff", "--no-color", "HEAD", "--", ...paths]);
	let patch = tracked.stdout;
	const untracked = new Set(
		splitNull((await git(pi, cwd, ["ls-files", "--others", "--exclude-standard", "-z", "--"])).stdout),
	);
	for (const path of paths) {
		if (!untracked.has(path)) continue;
		const result = await git(
			pi,
			cwd,
			["diff", "--no-index", "--no-ext-diff", "--no-color", "--", "/dev/null", path],
			true,
		);
		if (result.code !== 0 && result.code !== 1) {
			throw new Error(`Could not inspect untracked file ${path}: ${combinedOutput(result)}`);
		}
		patch += `\n${result.stdout}`;
	}
	if (Buffer.byteLength(patch) > MAX_PATCH_BYTES) {
		throw new Error(`The complete patch exceeds ${MAX_PATCH_BYTES / 1024}KB. Commit or scope part of the task first.`);
	}
	return patch;
}

export async function stagedPaths(pi: ExtensionAPI, cwd: string): Promise<string[]> {
	const result = await git(pi, cwd, ["diff", "--cached", "--name-only", "-z", "--"]);
	return splitNull(result.stdout).sort();
}

export async function createStagedSnapshot(pi: ExtensionAPI, repository: string) {
	const tree = (await git(pi, repository, ["write-tree"])).stdout.trim();
	const commit = (await git(pi, repository, [
		"commit-tree",
		tree,
		"-p",
		"HEAD",
		"-m",
		"Pi staged validation snapshot",
	])).stdout.trim();
	return createValidationWorktree(pi, repository, commit);
}
