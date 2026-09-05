import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const MAX_PATCH_BYTES = 256 * 1024;

function splitNull(value: string): string[] {
	return value.split("\0").filter(Boolean);
}

function pathsFromNameStatus(value: string): string[] {
	const fields = splitNull(value);
	const paths: string[] = [];
	for (let index = 0; index < fields.length;) {
		const status = fields[index++];
		const firstPath = fields[index++];
		if (firstPath) paths.push(firstPath);
		if (status?.startsWith("R") || status?.startsWith("C")) {
			const secondPath = fields[index++];
			if (secondPath) paths.push(secondPath);
		}
	}
	return [...new Set(paths)].sort();
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
	const tracked = await git(pi, cwd, ["diff", "--name-status", "-z", "HEAD", "--"]);
	const untracked = await git(pi, cwd, ["ls-files", "--others", "--exclude-standard", "-z", "--"]);
	return [...new Set([...pathsFromNameStatus(tracked.stdout), ...splitNull(untracked.stdout)])].sort();
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
	const result = await git(pi, cwd, ["diff", "--cached", "--name-status", "-z", "--"]);
	return pathsFromNameStatus(result.stdout);
}
