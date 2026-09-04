import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { StringEnum } from "@earendil-works/pi-ai";
import { Type } from "typebox";
import {
	formatValidationResult,
	getDirtyPaths,
	runVerification,
	type ValidationLevel,
} from "../../feedback/verification.js";

export const VALIDATION_STARTED_EVENT = "feedback:validation-started";
export const VALIDATION_RESULT_EVENT = "feedback:validation-result";

const PARAMETERS = Type.Object({
	level: Type.Optional(
		StringEnum(["fast", "test", "full"] as const, {
			description: "fast checks compilation/quality; test runs tests; full runs package or repository gates",
		}),
	),
	paths: Type.Optional(
		Type.Array(Type.String(), {
			description: "Repository-relative changed paths. Defaults to all dirty paths.",
		}),
	),
});

async function verify(
	pi: ExtensionAPI,
	cwd: string,
	level: ValidationLevel,
	paths: string[] | undefined,
	signal?: AbortSignal,
) {
	const selectedPaths = paths?.length ? [...new Set(paths)].sort() : await getDirtyPaths(pi, cwd);
	pi.events.emit(VALIDATION_STARTED_EVENT, { cwd, level, paths: selectedPaths });
	const result = await runVerification(pi, cwd, selectedPaths, level, signal);
	pi.events.emit(VALIDATION_RESULT_EVENT, result);
	return result;
}

export default function verifyChanges(pi: ExtensionAPI) {
	pi.registerTool({
		name: "verify_changes",
		label: "Verify Changes",
		description: "Run repository-aware validation for changed files. Output is limited to 160 lines or 16KB; complete truncated logs are saved under the system temporary directory.",
		promptSnippet: "Run scoped checks for changed files before reporting implementation work complete",
		promptGuidelines: [
			"Use verify_changes after modifying code and before claiming that implementation is complete.",
			"Start with verify_changes level fast; use test or full when the task warrants broader validation.",
		],
		parameters: PARAMETERS,
		async execute(_toolCallId, params, signal, onUpdate, ctx) {
			onUpdate?.({
				content: [{ type: "text", text: `Running ${params.level ?? "fast"} validation…` }],
				details: undefined,
			});
			const result = await verify(pi, ctx.cwd, params.level ?? "fast", params.paths, signal);
			return {
				content: [{ type: "text", text: formatValidationResult(result) }],
				details: result,
			};
		},
	});

	pi.registerCommand("verify", {
		description: "Run changed-file validation: /verify [fast|test|full]",
		handler: async (args, ctx) => {
			const requested = args.trim() || "fast";
			if (!(["fast", "test", "full"] as const).includes(requested as ValidationLevel)) {
				ctx.ui.notify("Usage: /verify [fast|test|full]", "warning");
				return;
			}
			const result = await verify(pi, ctx.cwd, requested as ValidationLevel, undefined, ctx.signal);
			ctx.ui.notify(result.passed ? "Validation passed." : "Validation failed; see the feedback widget.", result.passed ? "info" : "error");
		},
	});
}
