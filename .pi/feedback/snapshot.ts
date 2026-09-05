import { mkdtemp, rm } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";

function output(result: { stdout: string; stderr: string }): string {
	return [result.stdout, result.stderr].filter(Boolean).join("\n").trim();
}

export async function createValidationWorktree(
	pi: ExtensionAPI,
	repository: string,
	commit: string,
) {
	const parentDirectory = await mkdtemp(join(tmpdir(), "pi-validation-"));
	const worktree = join(parentDirectory, "worktree");
	const added = await pi.exec("git", [
		"-C",
		repository,
		"worktree",
		"add",
		"--quiet",
		"--detach",
		worktree,
		commit,
	]);
	if (added.code !== 0) {
		await rm(parentDirectory, { recursive: true, force: true });
		throw new Error(`Could not create validation worktree: ${output(added) || `exit ${added.code}`}`);
	}

	return {
		worktree,
		cleanup: async () => {
			const removed = await pi.exec("git", ["-C", repository, "worktree", "remove", "--force", worktree]);
			if (removed.code !== 0) {
				throw new Error(`Could not remove validation worktree: ${output(removed) || `exit ${removed.code}`}`);
			}
			await rm(parentDirectory, { recursive: true, force: true });
		},
	};
}
