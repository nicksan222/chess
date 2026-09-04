import { relative, resolve } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { changedPaths, snapshotDirtyFiles } from "../../feedback/verification.js";

export const FILES_CHANGED_EVENT = "feedback:files-changed";

export function attributedChanges(observedPaths: string[], explicitlyMutatedPaths: ReadonlySet<string>) {
	const explicitPaths = observedPaths.filter((path) => explicitlyMutatedPaths.has(path));
	const snapshotPaths = observedPaths.filter((path) => !explicitlyMutatedPaths.has(path));
	return {
		paths: observedPaths,
		explicitPaths,
		snapshotPaths,
		attribution: explicitPaths.length === 0 ? "snapshot" : snapshotPaths.length === 0 ? "tool" : "mixed",
	};
}

export function turnChangedPaths(
	before: Map<string, string>,
	after: Map<string, string>,
	committedPaths: readonly string[],
): string[] {
	return [...new Set([...changedPaths(before, after), ...committedPaths])].sort();
}

function repositoryPath(repository: string, cwd: string, inputPath: string): string | undefined {
	const path = relative(repository, resolve(cwd, inputPath)).replaceAll("\\", "/");
	if (!path || path === ".." || path.startsWith("../")) return undefined;
	return path;
}

async function currentHead(pi: ExtensionAPI, repository: string): Promise<string | undefined> {
	const result = await pi.exec("git", ["-C", repository, "rev-parse", "--verify", "HEAD"]);
	return result.code === 0 ? result.stdout.trim() : undefined;
}

async function committedChanges(
	pi: ExtensionAPI,
	repository: string,
	beforeHead: string | undefined,
): Promise<{ head: string | undefined; paths: string[] }> {
	const head = await currentHead(pi, repository);
	if (!beforeHead || !head || head === beforeHead) return { head, paths: [] };
	const result = await pi.exec("git", ["-C", repository, "diff", "--name-only", "-z", beforeHead, head, "--"]);
	const paths = result.code === 0
		? result.stdout.split("\0").filter((path) => path.length > 0)
		: [];
	return { head, paths };
}

export default function changeTracker(pi: ExtensionAPI) {
	let repository: string | undefined;
	let beforeHead: string | undefined;
	let beforeTurn = new Map<string, string>();
	const explicitlyMutatedPaths = new Set<string>();

	pi.on("turn_start", async (_event, ctx) => {
		explicitlyMutatedPaths.clear();
		const topLevel = await pi.exec("git", ["-C", ctx.cwd, "rev-parse", "--show-toplevel"]);
		repository = topLevel.code === 0 ? topLevel.stdout.trim() : undefined;
		if (!repository) {
			beforeHead = undefined;
			beforeTurn = new Map();
			return;
		}
		beforeHead = await currentHead(pi, repository);
		beforeTurn = await snapshotDirtyFiles(pi, repository);
	});

	pi.on("tool_call", (event, ctx) => {
		if (event.toolName !== "edit" && event.toolName !== "write") return;
		const input = event.input as { path?: unknown };
		if (typeof input.path !== "string") return;
		if (!repository) return;
		const path = repositoryPath(repository, ctx.cwd, input.path);
		if (path) explicitlyMutatedPaths.add(path);
	});

	pi.on("turn_end", async () => {
		if (!repository) return;
		const afterTurn = await snapshotDirtyFiles(pi, repository);
		const committed = await committedChanges(pi, repository, beforeHead);
		const observedPaths = turnChangedPaths(beforeTurn, afterTurn, committed.paths);
		beforeTurn = afterTurn;
		beforeHead = committed.head;
		if (observedPaths.length === 0) return;

		pi.events.emit(FILES_CHANGED_EVENT, {
			cwd: repository,
			...attributedChanges(observedPaths, explicitlyMutatedPaths),
			timestamp: Date.now(),
		});
	});
}
