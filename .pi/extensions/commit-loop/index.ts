import type { ExtensionAPI, ExtensionCommandContext } from "@earendil-works/pi-coding-agent";
import { formatValidationResult, runVerification } from "../../feedback/verification.js";
import { completePatch, dirtyPaths, git, stagedPaths } from "./git.js";
import { createCommitPlan, validateCommitPlan } from "./planner.js";

const REVIEW_PATCH_CHARACTERS = 16_000;

function conversationText(ctx: ExtensionCommandContext, maxCharacters = 12_000): string {
	const sections: string[] = [];
	for (const entry of ctx.sessionManager.getBranch()) {
		if (entry.type !== "message") continue;
		const message = entry.message;
		if (message.role !== "user" && message.role !== "assistant") continue;
		const content = message.content;
		const text = typeof content === "string"
			? content
			: content.filter((block) => block.type === "text").map((block) => block.text).join("\n");
		if (text.trim()) sections.push(`${message.role}: ${text.trim()}`);
	}
	return sections.join("\n\n").slice(-maxCharacters);
}

function reviewText(message: string, patch: string, index: number, total: number): string {
	const visiblePatch = patch.length <= REVIEW_PATCH_CHARACTERS
		? patch
		: `${patch.slice(0, REVIEW_PATCH_CHARACTERS)}\n\n[Patch truncated for review: ${patch.length - REVIEW_PATCH_CHARACTERS} characters omitted]`;
	return [
		`Staged commit ${index + 1}/${total}`,
		`Message: ${message}`,
		"",
		visiblePatch,
		"",
		"Is this tiny commit good, or does it need changes?",
	].join("\n");
}

async function unstage(pi: ExtensionAPI, cwd: string, paths: readonly string[]): Promise<void> {
	if (paths.length > 0) await git(pi, cwd, ["restore", "--staged", "--", ...paths]);
}

async function stageExact(pi: ExtensionAPI, cwd: string, paths: readonly string[]): Promise<void> {
	await git(pi, cwd, ["add", "--", ...paths]);
	const actual = await stagedPaths(pi, cwd);
	const expected = [...paths].sort();
	if (JSON.stringify(actual) !== JSON.stringify(expected)) {
		await unstage(pi, cwd, actual);
		throw new Error(`Staged paths differ from the plan. Expected ${expected.join(", ")}; found ${actual.join(", ") || "none"}.`);
	}
}

async function requestChanges(
	pi: ExtensionAPI,
	ctx: ExtensionCommandContext,
	repository: string,
	goal: string,
	message: string,
	paths: readonly string[],
): Promise<boolean> {
	const feedback = await ctx.ui.editor("Describe the changes needed in the patch or commit message");
	await unstage(pi, repository, paths);
	if (!feedback?.trim()) {
		ctx.ui.notify("Commit loop paused; staged changes were restored to the working tree.", "info");
		return false;
	}
	pi.events.emit("commit-loop:repair-requested", { goal, message, paths: [...paths], feedback: feedback.trim() });
	pi.sendUserMessage(
		[
			"Revise the next proposed tiny commit. Do not commit anything.",
			`Commit message: ${message}`,
			`Paths: ${paths.join(", ")}`,
			`Review feedback: ${feedback.trim()}`,
			"Preserve unrelated changes and stop after making and validating the requested revision.",
		].join("\n"),
	);
	return true;
}

async function runCommitLoop(
	pi: ExtensionAPI,
	ctx: ExtensionCommandContext,
	goal: string,
	setResumeGoal: (goal: string | undefined) => void,
): Promise<void> {
	if (!ctx.hasUI) throw new Error("/commit-loop requires TUI or RPC mode for staged-patch review.");
	await ctx.waitForIdle();
	const topLevel = await git(pi, ctx.cwd, ["rev-parse", "--show-toplevel"]);
	const repository = topLevel.stdout.trim();
	const paths = await dirtyPaths(pi, repository);
	if (paths.length === 0) throw new Error("There are no uncommitted changes to review.");
	const status = await git(pi, repository, ["status", "--short", "--branch"]);
	const recent = await git(pi, repository, ["log", "-8", "--pretty=format:%s"]);
	ctx.ui.setStatus("commit-loop", "planning tiny commits");
	const plan = await createCommitPlan(ctx, {
		goal,
		status: status.stdout.trim(),
		recentCommits: recent.stdout.trim(),
		conversation: conversationText(ctx),
		patch: await completePatch(pi, repository, paths),
	});
	const selectedPaths = validateCommitPlan(plan, paths);
	const selected = new Set(selectedPaths);
	const initiallyStaged = await stagedPaths(pi, repository);
	const unrelatedStaged = initiallyStaged.filter((path) => !selected.has(path));
	if (unrelatedStaged.length > 0) {
		throw new Error(`Refusing to alter the index because unrelated paths are staged: ${unrelatedStaged.join(", ")}`);
	}
	await unstage(pi, repository, initiallyStaged);

	const committed: string[] = [];
	for (const [index, commit] of plan.commits.entries()) {
		ctx.ui.setStatus("commit-loop", `staging ${index + 1}/${plan.commits.length}`);
		await stageExact(pi, repository, commit.paths);
		const stagedPatch = await git(pi, repository, ["diff", "--cached", "--no-ext-diff", "--no-color", "--"]);
		const choice = await ctx.ui.select(reviewText(commit.message, stagedPatch.stdout, index, plan.commits.length), [
			"Commit",
			"Needs changes",
			"Stop",
		]);

		if (choice === "Needs changes") {
			setResumeGoal(goal);
			if (!(await requestChanges(pi, ctx, repository, goal, commit.message, commit.paths))) setResumeGoal(undefined);
			return;
		}
		if (choice !== "Commit") {
			await unstage(pi, repository, commit.paths);
			ctx.ui.notify("Commit loop stopped; the proposed commit was unstaged.", "info");
			return;
		}

		ctx.ui.setStatus("commit-loop", `validating ${index + 1}/${plan.commits.length}`);
		const validation = await runVerification(pi, repository, commit.paths, "fast", ctx.signal);
		pi.events.emit("feedback:validation-result", validation);
		if (!validation.passed) {
			await unstage(pi, repository, commit.paths);
			throw new Error(`Commit validation failed; the proposed commit was unstaged.\n${formatValidationResult(validation)}`);
		}
		await git(pi, repository, ["commit", "-m", commit.message]);
		committed.push(commit.message.split("\n", 1)[0] ?? commit.message);
	}
	ctx.ui.notify(`Commit loop complete:\n${committed.map((message) => `- ${message}`).join("\n")}`, "info");
}

export default function commitLoop(pi: ExtensionAPI) {
	let resumeGoal: string | undefined;
	let resumeQueued = false;

	pi.registerCommand("commit-loop", {
		description: "Stage, review, validate, and create tiny sequential commits: /commit-loop [goal]",
		handler: async (args, ctx) => {
			resumeQueued = false;
			try {
				await runCommitLoop(pi, ctx, args.trim(), (goal) => {
					resumeGoal = goal;
				});
			} catch (error) {
				resumeGoal = undefined;
				ctx.ui.notify(error instanceof Error ? error.message : String(error), "error");
			} finally {
				ctx.ui.setStatus("commit-loop", undefined);
			}
		},
	});

	pi.on("agent_settled", () => {
		if (resumeGoal === undefined || resumeQueued) return;
		const goal = resumeGoal;
		resumeGoal = undefined;
		resumeQueued = true;
		queueMicrotask(() => {
			pi.sendUserMessage(`/commit-loop${goal ? ` ${goal}` : ""}`, { expandPromptTemplates: true });
		});
	});
}
