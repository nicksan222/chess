import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import type { ExtensionAPI, ExtensionCommandContext } from "@earendil-works/pi-coding-agent";
import { pathsFromNameStatus } from "../../feedback/git-paths.js";
import { suspiciousPatchLines, suspiciousTextLines } from "../../feedback/secrets.js";
import { createValidationWorktree } from "../../feedback/snapshot.js";
import { formatValidationResult, preparePiDependencies, runVerification } from "../../feedback/verification.js";
import {
	git,
	inspectGitState,
	validateBranchName,
	type GitState,
} from "./git.js";
import { conversationText, createPrPlan, validatePrPlan, type PrPlan } from "./planner.js";

function targetBranch(state: GitState, plannedBranch: string): string {
	return state.currentBranch === "HEAD" || state.currentBranch === state.baseBranch || state.currentBranch.startsWith("pi/")
		? plannedBranch
		: state.currentBranch;
}

function planPreview(state: GitState, plan: PrPlan, branch: string): string {
	const plannedCommits = plan.commits.length > 0
		? plan.commits
			.map((commit, index) => `${index + 1}. ${commit.message.split("\n", 1)[0]}\n   ${commit.paths.join(", ")}`)
			.join("\n")
		: "(none; publish existing commits only)";
	const existingCommits = state.existingCommits || "(none)";
	const remote = state.canPublish
		? `push ${branch} to origin and create a GitHub PR against ${state.baseBranch}`
		: `create local branch and commits only (${state.publishProblem})`;
	return [
		`Branch: ${branch}`,
		`Base: ${state.baseBranch}`,
		"Existing commits:",
		existingCommits,
		"",
		"Planned commits:",
		plannedCommits,
		"",
		`PR title: ${plan.title}`,
		plan.body,
		"",
		`Action: ${remote}`,
	].join("\n");
}

async function createBranch(pi: ExtensionAPI, state: GitState, branch: string): Promise<void> {
	if (branch === state.currentBranch) return;
	if (state.currentBranch.startsWith("pi/")) {
		await git(pi, state.repository, ["branch", "-m", branch]);
		return;
	}
	await git(pi, state.repository, ["switch", "-c", branch]);
}

async function createCommits(
	pi: ExtensionAPI,
	ctx: ExtensionCommandContext,
	state: GitState,
	plan: PrPlan,
): Promise<void> {
	const selected = new Set(plan.commits.flatMap((commit) => commit.paths));
	const unrelatedStaged = state.stagedPaths.filter((path) => !selected.has(path));
	let savedIndexDirectory: string | undefined;
	try {
		if (unrelatedStaged.length > 0) {
			const patch = await git(pi, state.repository, [
				"diff", "--cached", "--binary", "--full-index", "--", ...unrelatedStaged,
			]);
			savedIndexDirectory = await mkdtemp(join(tmpdir(), "pi-pr-index-"));
			await writeFile(join(savedIndexDirectory, "unrelated.patch"), patch.stdout);
			await git(pi, state.repository, ["restore", "--staged", "--", ...unrelatedStaged]);
		}
		const selectedStaged = state.stagedPaths.filter((path) => selected.has(path));
		if (selectedStaged.length > 0) {
			await git(pi, state.repository, ["restore", "--staged", "--", ...selectedStaged]);
		}

		for (const [index, commit] of plan.commits.entries()) {
			ctx.ui.setStatus("pr-workflow", `committing ${index + 1}/${plan.commits.length}`);
			await git(pi, state.repository, ["add", "--", ...commit.paths]);
			const staged = await git(pi, state.repository, ["diff", "--cached", "--name-status", "-z", "--"]);
			const actualPaths = pathsFromNameStatus(staged.stdout);
			const expectedPaths = [...commit.paths].sort();
			if (JSON.stringify(actualPaths) !== JSON.stringify(expectedPaths)) {
				throw new Error(`Staged paths differ from commit plan. Expected ${expectedPaths.join(", ")}; found ${actualPaths.join(", ") || "none"}.`);
			}
			await git(pi, state.repository, ["commit", "--no-verify", "-m", commit.message]);
		}
	} finally {
		if (savedIndexDirectory) {
			await git(pi, state.repository, ["apply", "--cached", join(savedIndexDirectory, "unrelated.patch")]);
			await rm(savedIndexDirectory, { recursive: true, force: true });
		}
	}
}

async function reviewCommits(
	pi: ExtensionAPI,
	state: GitState,
	selectedPaths: readonly string[],
): Promise<string> {
	if (selectedPaths.length > 0) {
		const remaining = await git(pi, state.repository, ["status", "--porcelain", "--", ...selectedPaths]);
		if (remaining.stdout.trim()) {
			throw new Error(`Selected task paths remain uncommitted:\n${remaining.stdout.trim()}`);
		}
	}
	await git(pi, state.repository, ["diff", "--check", `${state.baseOid}..HEAD`, "--"]);
	const log = await git(pi, state.repository, [
		"log",
		"--reverse",
		"--pretty=format:%h %s",
		`${state.baseOid}..HEAD`,
	]);
	return log.stdout.trim();
}

async function publish(
	pi: ExtensionAPI,
	state: GitState,
	branch: string,
	plan: PrPlan,
): Promise<string> {
	await git(pi, state.repository, ["push", "--set-upstream", "origin", branch]);
	const result = await pi.exec("gh", [
		"pr",
		"create",
		"--base",
		state.baseBranch,
		"--head",
		branch,
		"--title",
		plan.title,
		"--body",
		plan.body,
	]);
	if (result.code !== 0) {
		throw new Error(
			`Branch was pushed, but PR creation failed: ${[result.stderr, result.stdout].filter(Boolean).join("\n").trim()}\nRetry: gh pr create --base ${state.baseBranch} --head ${branch}`,
		);
	}
	return result.stdout.trim();
}

async function runPr(pi: ExtensionAPI, args: string, ctx: ExtensionCommandContext): Promise<void> {
	if (!ctx.hasUI) throw new Error("/pr requires TUI or RPC mode for publish confirmation.");
	await ctx.waitForIdle();
	ctx.ui.setStatus("pr-workflow", "inspecting changes");
	const state = await inspectGitState(pi, ctx.cwd);
	const suspicious = [
		...suspiciousTextLines(state.existingCommits),
		...suspiciousPatchLines(`${state.existingPatch}\n${state.patch}`),
	].slice(0, 5);
	if (suspicious.length > 0) {
		throw new Error(`Potential secret material found in outgoing changes; inspect before retrying:\n${suspicious.join("\n")}`);
	}

	ctx.ui.setStatus("pr-workflow", "planning commits");
	const plan = await createPrPlan(ctx, {
		goal: args.trim(),
		currentBranch: state.currentBranch,
		baseBranch: state.baseBranch,
		status: state.status,
		existingCommits: state.existingCommits,
		existingPatch: state.existingPatch,
		recentCommits: state.recentCommits,
		conversation: conversationText(ctx),
		patch: state.patch,
	});
	const selectedPaths = validatePrPlan(plan, state.dirtyPaths, state.existingCommits.length > 0);
	const branch = targetBranch(state, plan.branch);
	await validateBranchName(pi, state, branch);

	const approved = await ctx.ui.confirm("Create and publish pull request?", planPreview(state, plan, branch));
	if (!approved) {
		ctx.ui.notify("PR preparation cancelled without changing Git state.", "info");
		return;
	}

	await createBranch(pi, state, branch);
	await createCommits(pi, ctx, state, plan);
	ctx.ui.setStatus("pr-workflow", "running full validation");
	const validationPaths = [...new Set([...state.existingPaths, ...selectedPaths])].sort();
	const snapshot = await createValidationWorktree(pi, state.repository, "HEAD");
	let validation;
	try {
		await preparePiDependencies(pi, snapshot.worktree, validationPaths, ctx.signal);
		validation = await runVerification(pi, snapshot.worktree, validationPaths, "full", ctx.signal);
	} finally {
		await snapshot.cleanup();
	}
	pi.events.emit("feedback:validation-result", validation);
	if (!validation.passed) {
		throw new Error(`Commits were created, but publishing was stopped because validation failed.\n${formatValidationResult(validation)}`);
	}

	ctx.ui.setStatus("pr-workflow", "reviewing commit range");
	const commitLog = await reviewCommits(pi, state, selectedPaths);
	if (!state.canPublish) {
		ctx.ui.notify(
			`Created and validated local commits:\n${commitLog}\n${state.publishProblem}\nNext: git push --set-upstream origin ${branch}`,
			"warning",
		);
		return;
	}

	ctx.ui.setStatus("pr-workflow", "publishing PR");
	const url = await publish(pi, state, branch, plan);
	pi.setSessionName(plan.title);
	ctx.ui.notify(`Pull request created: ${url}`, "info");
}

export default function prWorkflow(pi: ExtensionAPI) {
	pi.registerCommand("pr", {
		description: "Plan, commit, validate, push, and create a pull request: /pr [goal]",
		handler: async (args, ctx) => {
			try {
				await runPr(pi, args, ctx);
			} catch (error) {
				ctx.ui.notify(error instanceof Error ? error.message : String(error), "error");
			} finally {
				ctx.ui.setStatus("pr-workflow", undefined);
			}
		},
	});
}
