import {
	Type,
	type Static,
	type Tool,
	uuidv7,
	validateToolCall,
} from "@earendil-works/pi-ai";
import type { ExtensionCommandContext } from "@earendil-works/pi-coding-agent";

const COMMIT_SCHEMA = Type.Object(
	{
		message: Type.String({ minLength: 3, description: "Imperative commit subject, optionally followed by a body" }),
		paths: Type.Array(Type.String({ minLength: 1 }), { minItems: 1 }),
	},
	{ additionalProperties: false },
);

const PLAN_SCHEMA = Type.Object(
	{
		commits: Type.Array(COMMIT_SCHEMA, { minItems: 1 }),
	},
	{ additionalProperties: false },
);

export type CommitPlan = Static<typeof PLAN_SCHEMA>;

const PLANNING_TOOL: Tool = {
	name: "submit_commit_plan",
	description: "Submit the ordered tiny-commit plan",
	parameters: PLAN_SCHEMA,
	constrainedSampling: { type: "json_schema", strict: "prefer" },
};

export interface CommitPlanningInput {
	goal: string;
	status: string;
	recentCommits: string;
	conversation: string;
	patch: string;
}

export async function createCommitPlan(
	ctx: ExtensionCommandContext,
	input: CommitPlanningInput,
): Promise<CommitPlan> {
	const model = ctx.model;
	if (!model) throw new Error("No active model is available for commit planning.");
	if (!ctx.modelRegistry.hasConfiguredAuth(model)) {
		throw new Error(`No authentication is configured for ${model.provider}/${model.id}.`);
	}

	const prompt = [
		"Plan the smallest useful ordered Git commits for the task below.",
		"Call submit_commit_plan exactly once and emit no prose.",
		"Select only dirty paths belonging to the goal and conversation; omit unrelated work.",
		"A path may occur in only one commit. Keep inseparable same-file changes together.",
		"Every commit must be independently understandable and build on the previous commits.",
		"Use imperative messages matching recent repository style.",
		"",
		`Goal: ${input.goal || "Infer the current task from the conversation."}`,
		"",
		"<conversation>",
		input.conversation,
		"</conversation>",
		"",
		"<status>",
		input.status,
		"</status>",
		"",
		"<recent-commits>",
		input.recentCommits,
		"</recent-commits>",
		"",
		"<complete-patch>",
		input.patch,
		"</complete-patch>",
	].join("\n");

	const response = await ctx.modelRegistry.complete(
		model,
		{
			systemPrompt: "You are a precise Git commit planner. Return plans only through the supplied tool.",
			messages: [{ role: "user", content: [{ type: "text", text: prompt }], timestamp: Date.now() }],
			tools: [PLANNING_TOOL],
		},
		{ cacheRetention: "none", sessionId: uuidv7(), signal: ctx.signal },
	);
	if (response.stopReason === "error" || response.stopReason === "aborted") {
		throw new Error(response.errorMessage || `Commit planning ${response.stopReason}.`);
	}
	const call = response.content.find(
		(block): block is Extract<(typeof response.content)[number], { type: "toolCall" }> =>
			block.type === "toolCall" && block.name === PLANNING_TOOL.name,
	);
	if (!call) throw new Error("The model did not return a commit plan.");
	return validateToolCall([PLANNING_TOOL], call) as CommitPlan;
}

export function validateCommitPlan(plan: CommitPlan, dirtyPaths: readonly string[]): string[] {
	const allowed = new Set(dirtyPaths);
	const selected = new Set<string>();
	for (const commit of plan.commits) {
		for (const path of commit.paths) {
			if (!allowed.has(path)) throw new Error(`Commit plan selected a path that is not dirty: ${path}`);
			if (selected.has(path)) throw new Error(`Commit plan selected the same path more than once: ${path}`);
			selected.add(path);
		}
	}
	return [...selected];
}
