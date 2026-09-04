import type { ExtensionAPI, ExtensionContext } from "@earendil-works/pi-coding-agent";
import type { ValidationResult } from "../../feedback/verification.js";

const VALIDATION_STARTED_EVENT = "feedback:validation-started";
const VALIDATION_RESULT_EVENT = "feedback:validation-result";
const STATUS_KEY = "validation-feedback";
const WIDGET_KEY = "validation-feedback";

interface ValidationStartedEvent {
	level: string;
	paths: string[];
}

function updateResult(ctx: ExtensionContext, result: ValidationResult): void {
	const theme = ctx.ui.theme;
	if (result.passed) {
		ctx.ui.setStatus(STATUS_KEY, theme.fg("success", `✓ ${result.level} validation`));
		ctx.ui.setWidget(WIDGET_KEY, undefined);
		return;
	}

	ctx.ui.setStatus(STATUS_KEY, theme.fg("error", `✗ ${result.level} validation`));
	const failed = result.checks.find((check) => check.code !== 0);
	const diagnostics = failed?.output.split("\n").filter(Boolean).slice(-8) ?? [];
	ctx.ui.setWidget(
		WIDGET_KEY,
		[
			theme.fg("error", "Validation failed"),
			...(failed ? [theme.fg("muted", failed.command)] : []),
			...diagnostics.map((line) => theme.fg("dim", line)),
			...(failed?.fullOutputPath ? [theme.fg("muted", `Full log: ${failed.fullOutputPath}`)] : []),
		],
	);
}

export default function validationStatus(pi: ExtensionAPI) {
	let currentContext: ExtensionContext | undefined;

	pi.on("session_start", (_event, ctx) => {
		currentContext = ctx;
		ctx.ui.setStatus(STATUS_KEY, ctx.ui.theme.fg("dim", "validation ready"));
	});

	pi.events.on(VALIDATION_STARTED_EVENT, (data) => {
		const event = data as ValidationStartedEvent;
		const ctx = currentContext;
		if (!ctx) return;
		ctx.ui.setStatus(
			STATUS_KEY,
			ctx.ui.theme.fg("accent", `● checking ${event.paths.length} path${event.paths.length === 1 ? "" : "s"} (${event.level})`),
		);
	});

	pi.events.on(VALIDATION_RESULT_EVENT, (data) => {
		if (currentContext) updateResult(currentContext, data as ValidationResult);
	});

	pi.registerCommand("validation-clear", {
		description: "Clear validation feedback from the status line and editor widget",
		handler: async (_args, ctx) => {
			ctx.ui.setWidget(WIDGET_KEY, undefined);
			ctx.ui.setStatus(STATUS_KEY, ctx.ui.theme.fg("dim", "validation ready"));
		},
	});

	pi.on("session_shutdown", (_event, ctx) => {
		ctx.ui.setStatus(STATUS_KEY, undefined);
		ctx.ui.setWidget(WIDGET_KEY, undefined);
		currentContext = undefined;
	});
}
