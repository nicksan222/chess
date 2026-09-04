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

function repositoryPath(cwd: string, inputPath: string): string | undefined {
	const path = relative(cwd, resolve(cwd, inputPath)).replaceAll("\\", "/");
	if (!path || path === ".." || path.startsWith("../")) return undefined;
	return path;
}

export default function changeTracker(pi: ExtensionAPI) {
	let beforeTurn = new Map<string, string>();
	const explicitlyMutatedPaths = new Set<string>();

	pi.on("turn_start", async (_event, ctx) => {
		explicitlyMutatedPaths.clear();
		beforeTurn = await snapshotDirtyFiles(pi, ctx.cwd);
	});

	pi.on("tool_call", (event, ctx) => {
		if (event.toolName !== "edit" && event.toolName !== "write") return;
		const input = event.input as { path?: unknown };
		if (typeof input.path !== "string") return;
		const path = repositoryPath(ctx.cwd, input.path);
		if (path) explicitlyMutatedPaths.add(path);
	});

	pi.on("turn_end", async (_event, ctx) => {
		const afterTurn = await snapshotDirtyFiles(pi, ctx.cwd);
		const observedPaths = changedPaths(beforeTurn, afterTurn);
		beforeTurn = afterTurn;
		if (observedPaths.length === 0) return;

		pi.events.emit(FILES_CHANGED_EVENT, {
			cwd: ctx.cwd,
			...attributedChanges(observedPaths, explicitlyMutatedPaths),
			timestamp: Date.now(),
		});
	});
}
