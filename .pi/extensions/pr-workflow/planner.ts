import {
	StringEnum,
	Type,
	type AssistantMessage,
	type Static,
	type Tool,
	uuidv7,
	validateToolCall,
} from "@earendil-works/pi-ai";
import type { ExtensionCommandContext } from "@earendil-works/pi-coding-agent";

const COMMIT_SCHEMA = Type.Object(
	{
		message: Type.String({ minLength: 3, description: "Imperative commit subject, optionally followed by a body" }),
		paths: Type.Array(Type.String({ minLength: 1 }), {
			minItems: 1,
			description: "Repository-relative paths owned by this commit",
		}),
	},
	{ additionalProperties: false },
);

const PLAN_SCHEMA = Type.Object(
	{
		branch: Type.String({
			minLength: 3,
			description: "Semantic branch name using type/short-kebab-case-goal",
		}),
		title: Type.String({ minLength: 5, maxLength: 90 }),
		body: Type.String({
			minLength: 10,
			description: "Pull request body containing Summary and Validation Markdown sections",
		}),
		commits: Type.Array(COMMIT_SCHEMA, {
			description: "Small ordered commits. A path may belong to only one commit.",
		}),
	},
	{ additionalProperties: false },
);

export type PrPlan = Static<typeof PLAN_SCHEMA>;

const PLANNING_TOOL: Tool = {
	name: "submit_pr_plan",
	description: "Submit the final branch, commit, and pull-request plan",
	parameters: PLAN_SCHEMA,
	constrainedSampling: { type: "json_schema", strict: "prefer" },
};

export interface PlanningInput {
	goal: string;
	currentBranch: string;
	baseBranch: string;
	status: string;
	existingCommits: string;
	existingPatch: string;
	recentCommits: string;
	conversation: string;
	patch: string;
}

function planningPrompt(input: PlanningInput): string {
	return [
		"Plan a high-quality pull request from the repository state below.",
		"Call submit_pr_plan exactly once and emit no prose.",
		"Choose only changes belonging to the stated goal and conversation; omit unrelated dirty paths.",
		"Group selected dirty paths into the smallest useful ordered commits. A path can occur in only one commit, so keep inseparable same-file changes together.",
		"Existing commits are already part of the pull request: describe them in the title and body, but do not recreate them. If there are no dirty task changes, return an empty commits array.",
		"Use imperative commit subjects matching recent repository style.",
		"Use a semantic branch name: feat/, fix/, refactor/, docs/, test/, ci/, build/, perf/, or chore/ followed by concise kebab-case.",
		"The PR body must contain '## Summary' and '## Validation' sections. Under Validation, record that the repository pre-commit hook runs for every generated commit.",
		"Never select secrets, credentials, temporary logs, build output, or unrelated generated files.",
		"",
		`Goal: ${input.goal || "Infer the goal from the conversation."}`,
		`Current branch: ${input.currentBranch}`,
		`Base branch: ${input.baseBranch}`,
		"",
		"<conversation>",
		input.conversation,
		"</conversation>",
		"",
		"<status>",
		input.status,
		"</status>",
		"",
		"<existing-pr-commits>",
		input.existingCommits || "(none)",
		"</existing-pr-commits>",
		"",
		"<recent-commits>",
		input.recentCommits,
		"</recent-commits>",
		"",
		"<existing-commit-patch>",
		input.existingPatch || "(none)",
		"</existing-commit-patch>",
		"",
		"<dirty-patch>",
		input.patch || "(none)",
		"</dirty-patch>",
	].join("\n");
}

export async function createPrPlan(
	ctx: ExtensionCommandContext,
	input: PlanningInput,
	onThinking?: (thinking: string) => void,
): Promise<PrPlan> {
	const model = ctx.model;
	if (!model) throw new Error("No active model is available for PR planning.");
	if (!ctx.modelRegistry.hasConfiguredAuth(model)) {
		throw new Error(`No authentication is configured for ${model.provider}/${model.id}.`);
	}

	const context = {
		systemPrompt: "You are a precise release engineer. Return plans only through the supplied tool.",
		messages: [
			{
				role: "user" as const,
				content: [{ type: "text" as const, text: planningPrompt(input) }],
				timestamp: Date.now(),
			},
		],
		tools: [PLANNING_TOOL],
	};
	const options = {
		cacheRetention: "none" as const,
		sessionId: uuidv7(),
		signal: ctx.signal,
	};
	let response: AssistantMessage;
	if (onThinking) {
		const auth = await ctx.modelRegistry.getApiKeyAndHeaders(model);
		if (!auth.ok) throw new Error(auth.error);
		const provider = ctx.modelRegistry.getProvider(model.provider);
		if (!provider) throw new Error(`Provider is not available: ${model.provider}`);
		const requestModel = auth.baseUrl ? { ...model, baseUrl: auth.baseUrl } : model;
		const stream = provider.stream(requestModel, context, {
			...options,
			apiKey: auth.apiKey,
			headers: auth.headers,
			env: auth.env,
		});
		let thinking = "";
		for await (const event of stream) {
			if (event.type === "thinking_delta") {
				thinking += event.delta;
				onThinking(thinking);
			} else if (event.type === "thinking_end") {
				thinking = event.content;
				onThinking(thinking);
			}
		}
		response = await stream.result();
	} else {
		response = await ctx.modelRegistry.complete(model, context, options);
	}
	if (response.stopReason === "error" || response.stopReason === "aborted") {
		throw new Error(response.errorMessage || `PR planning ${response.stopReason}.`);
	}

	const call = response.content.find(
		(block): block is Extract<(typeof response.content)[number], { type: "toolCall" }> =>
			block.type === "toolCall" && block.name === PLANNING_TOOL.name,
	);
	if (!call) throw new Error("The model did not return a PR plan.");
	return validateToolCall([PLANNING_TOOL], call) as PrPlan;
}

export function validatePrPlan(plan: PrPlan, dirtyPaths: readonly string[], allowEmpty = false): string[] {
	const allowed = new Set(dirtyPaths);
	const selected = new Set<string>();
	for (const commit of plan.commits) {
		const expandedPaths: string[] = [];
		for (const selector of commit.paths) {
			const matches = allowed.has(selector)
				? [selector]
				: selector.endsWith("/")
					? dirtyPaths.filter((path) => path.startsWith(selector))
					: [];
			if (matches.length === 0) throw new Error(`PR plan selected a path that is not dirty: ${selector}`);
			for (const path of matches) {
				if (selected.has(path)) throw new Error(`PR plan selected the same path more than once: ${path}`);
				selected.add(path);
				expandedPaths.push(path);
			}
		}
		commit.paths = expandedPaths;
	}
	if (selected.size === 0 && !allowEmpty) throw new Error("PR plan did not select any task changes.");
	if (!/^(feat|fix|refactor|docs|test|ci|build|perf|chore)\/[a-z0-9]+(?:-[a-z0-9]+)*$/.test(plan.branch)) {
		throw new Error(`PR plan returned an invalid semantic branch name: ${plan.branch}`);
	}
	if (!/^## Summary\b/m.test(plan.body) || !/^## Validation\b/m.test(plan.body)) {
		throw new Error("PR body must contain ## Summary and ## Validation sections.");
	}
	return [...selected];
}

export function conversationText(ctx: ExtensionCommandContext, maxCharacters = 12_000): string {
	const sections: string[] = [];
	for (const entry of ctx.sessionManager.getBranch()) {
		if (entry.type !== "message") continue;
		const message = entry.message;
		if (message.role !== "user" && message.role !== "assistant") continue;
		const content = message.content;
		const text = typeof content === "string"
			? content
			: content
				.filter((block) => block.type === "text")
				.map((block) => block.text)
				.join("\n");
		if (text.trim()) sections.push(`${message.role}: ${text.trim()}`);
	}
	return sections.join("\n\n").slice(-maxCharacters);
}
