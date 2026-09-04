import { relative, resolve } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { changedPaths, snapshotDirtyFiles } from "../../feedback/verification.js";

export const FILES_CHANGED_EVENT = "feedback:files-changed";

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
		const paths = explicitlyMutatedPaths.size > 0
			? observedPaths.filter((path) => explicitlyMutatedPaths.has(path))
			: observedPaths;
		if (paths.length === 0) return;

		pi.events.emit(FILES_CHANGED_EVENT, {
			cwd: ctx.cwd,
			paths,
			attribution: explicitlyMutatedPaths.size > 0 ? "tool" : "snapshot",
			timestamp: Date.now(),
		});
	});
}
