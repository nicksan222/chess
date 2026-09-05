import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

const MAX_PATCH_BYTES = 256 * 1024;
const SECRET_PATTERNS = [
	/[a-z0-9_-]*(?:api[-_]?key|secret|password|token)[a-z0-9_-]*["']?\s*[:=]\s*["'][^"']{8,}/i,
	/^\+\s*(?:-\s+)?(?:export\s+)?["']?[a-z0-9_-]*(?:api[-_]?key|secret|password|token)[a-z0-9_-]*["']?\s*[:=]\s*[^\s#"']{8,}\s*(?:#.*)?$/i,
	/-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----/,
	/ghp_[A-Za-z0-9]{20,}/,
	/github_pat_[A-Za-z0-9_]{20,}/,
	/sk-[A-Za-z0-9_-]{20,}/,
];

function splitNull(value: string): string[] {
	return value.split("\0").filter(Boolean);
}

export function pathsFromNameStatus(value: string): string[] {
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

export function suspiciousTextLines(text: string): string[] {
	return text.split("\n")
		.filter((line) => SECRET_PATTERNS.some((pattern) => pattern.test(line) || pattern.test(`+${line}`)))
		.slice(0, 5);
}

export function suspiciousPatchLines(patch: string): string[] {
	return suspiciousTextLines(
		patch.split("\n").filter((line) => line.startsWith("+") && !line.startsWith("+++")).join("\n"),
	);
}

export interface GitState {
	repository: string;
	currentBranch: string;
	baseBranch: string;
	baseOid: string;
	existingCommits: string;
	existingPatch: string;
	dirtyPaths: string[];
	stagedPaths: string[];
	status: string;
	recentCommits: string;
	patch: string;
	originUrl?: string;
	canPublish: boolean;
	publishProblem?: string;
}

function output(result: { stdout: string; stderr: string }): string {
	return [result.stdout, result.stderr].filter(Boolean).join("\n").trim();
}

export async function git(pi: ExtensionAPI, cwd: string, args: string[], allowFailure = false) {
	const result = await pi.exec("git", ["-C", cwd, ...args]);
	if (!allowFailure && result.code !== 0) {
		throw new Error(`git ${args.join(" ")} failed: ${output(result) || `exit ${result.code}`}`);
	}
	return result;
}

async function dirtyPaths(pi: ExtensionAPI, cwd: string): Promise<string[]> {
	const tracked = await git(pi, cwd, ["diff", "--name-status", "-z", "HEAD", "--"]);
	const untracked = await git(pi, cwd, ["ls-files", "--others", "--exclude-standard", "-z", "--"]);
	return [...new Set([...pathsFromNameStatus(tracked.stdout), ...splitNull(untracked.stdout)])].sort();
}

async function completePatch(pi: ExtensionAPI, cwd: string, paths: readonly string[]): Promise<string> {
	const tracked = await git(pi, cwd, ["diff", "--no-ext-diff", "--no-color", "HEAD", "--", ...paths]);
	let patch = tracked.stdout;
	const untracked = new Set(splitNull((await git(pi, cwd, ["ls-files", "--others", "--exclude-standard", "-z", "--"])).stdout));
	for (const path of paths) {
		if (!untracked.has(path)) continue;
		const result = await git(pi, cwd, ["diff", "--no-index", "--no-ext-diff", "--no-color", "--", "/dev/null", path], true);
		if (result.code !== 0 && result.code !== 1) {
			throw new Error(`Could not inspect untracked file ${path}: ${output(result)}`);
		}
		patch += `\n${result.stdout}`;
	}
	if (Buffer.byteLength(patch) > MAX_PATCH_BYTES) {
		throw new Error(`The complete patch exceeds ${MAX_PATCH_BYTES / 1024}KB. Commit or scope part of the task before running /pr.`);
	}
	return patch;
}

async function baseBranch(pi: ExtensionAPI, cwd: string): Promise<string> {
	const symbolic = await git(pi, cwd, ["symbolic-ref", "--quiet", "--short", "refs/remotes/origin/HEAD"], true);
	if (symbolic.code === 0 && symbolic.stdout.trim().startsWith("origin/")) {
		return symbolic.stdout.trim().slice("origin/".length);
	}
	for (const candidate of ["main", "master"]) {
		if ((await git(pi, cwd, ["show-ref", "--verify", "--quiet", `refs/remotes/origin/${candidate}`], true)).code === 0) {
			return candidate;
		}
	}
	for (const candidate of ["main", "master"]) {
		if ((await git(pi, cwd, ["show-ref", "--verify", "--quiet", `refs/heads/${candidate}`], true)).code === 0) {
			return candidate;
		}
	}
	throw new Error("Could not find a main or master base branch locally or on origin.");
}

export async function inspectGitState(pi: ExtensionAPI, cwd: string): Promise<GitState> {
	const topLevel = await git(pi, cwd, ["rev-parse", "--show-toplevel"]);
	const repository = topLevel.stdout.trim();
	const branchResult = await git(pi, repository, ["symbolic-ref", "--quiet", "--short", "HEAD"], true);
	const currentBranch = branchResult.code === 0 ? branchResult.stdout.trim() : "HEAD";
	const selectedBase = await baseBranch(pi, repository);
	const remoteBase = `origin/${selectedBase}`;
	let mergeBase = await git(pi, repository, ["merge-base", "HEAD", remoteBase], true);
	if (mergeBase.code !== 0) {
		mergeBase = await git(pi, repository, ["merge-base", "HEAD", selectedBase], true);
	}
	if (mergeBase.code !== 0) {
		throw new Error(`Could not resolve a merge base against ${remoteBase} or local ${selectedBase}.`);
	}
	const baseOid = mergeBase.stdout.trim();
	const existingCommits = (await git(pi, repository, [
		"log",
		"--reverse",
		"--pretty=format:%h %s%n%b",
		`${baseOid}..HEAD`,
	])).stdout.trim();
	const existingPatch = (await git(pi, repository, [
		"log",
		"--reverse",
		"--format=",
		"--patch",
		"--diff-merges=first-parent",
		"--no-ext-diff",
		"--no-color",
		`${baseOid}..HEAD`,
		"--",
	])).stdout;
	if (Buffer.byteLength(existingPatch) > MAX_PATCH_BYTES) {
		throw new Error(`The committed patch exceeds ${MAX_PATCH_BYTES / 1024}KB. Review and publish it manually.`);
	}
	const paths = await dirtyPaths(pi, repository);
	if (paths.length === 0 && !existingCommits) {
		throw new Error("There are no commits or uncommitted changes to prepare.");
	}

	const status = await git(pi, repository, ["status", "--short", "--branch"]);
	const staged = await git(pi, repository, ["diff", "--cached", "--name-status", "-z", "--"]);
	const recent = await git(pi, repository, ["log", "-8", "--pretty=format:%s"]);
	const origin = await git(pi, repository, ["remote", "get-url", "origin"], true);
	const gh = await pi.exec("gh", ["auth", "status"]);
	const originUrl = origin.code === 0 ? origin.stdout.trim() : undefined;
	const canPublish = Boolean(originUrl) && gh.code === 0;
	const publishProblem = !originUrl
		? "Git remote 'origin' is not configured."
		: gh.code !== 0
			? `GitHub CLI authentication is unavailable: ${output(gh) || `exit ${gh.code}`}`
			: undefined;

	return {
		repository,
		currentBranch,
		baseBranch: selectedBase,
		baseOid,
		existingCommits,
		existingPatch,
		dirtyPaths: paths,
		stagedPaths: pathsFromNameStatus(staged.stdout),
		status: status.stdout.trim(),
		recentCommits: recent.stdout.trim(),
		patch: await completePatch(pi, repository, paths),
		originUrl,
		canPublish,
		publishProblem,
	};
}

export async function validateBranchName(pi: ExtensionAPI, state: GitState, branch: string): Promise<void> {
	const format = await git(pi, state.repository, ["check-ref-format", "--branch", branch], true);
	if (format.code !== 0) throw new Error(`Invalid branch name ${branch}: ${output(format)}`);
	if (branch === state.currentBranch) return;
	const collision = await git(pi, state.repository, ["show-ref", "--verify", "--quiet", `refs/heads/${branch}`], true);
	if (collision.code === 0) throw new Error(`Local branch already exists: ${branch}`);
}
