import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { formatValidationResult, runVerification } from "../../feedback/verification.js";

const FILES_CHANGED_EVENT = "feedback:files-changed";
const VALIDATION_STARTED_EVENT = "feedback:validation-started";
const VALIDATION_RESULT_EVENT = "feedback:validation-result";
const MAX_AUTOMATIC_REPAIR_ROUNDS = 2;

interface FilesChangedEvent {
	cwd: string;
	paths: string[];
}

export default function autoValidation(pi: ExtensionAPI) {
	const pendingPaths = new Set<string>();
	let pendingCwd: string | undefined;
	let lastFailureFingerprint: string | undefined;
	let automaticRepairRounds = 0;
	let checking = false;

	pi.events.on(FILES_CHANGED_EVENT, (data) => {
		const event = data as FilesChangedEvent;
		pendingCwd = event.cwd;
		for (const path of event.paths) pendingPaths.add(path);
	});

	pi.on("session_start", () => {
		pendingPaths.clear();
		pendingCwd = undefined;
		lastFailureFingerprint = undefined;
		automaticRepairRounds = 0;
		checking = false;
	});

	pi.on("agent_end", async (_event, ctx) => {
		if (checking || pendingPaths.size === 0 || pendingCwd !== ctx.cwd) return;

		checking = true;
		const paths = [...pendingPaths].sort();
		pendingPaths.clear();
		pi.events.emit(VALIDATION_STARTED_EVENT, { cwd: ctx.cwd, level: "fast", paths });

		try {
			const result = await runVerification(pi, ctx.cwd, paths, "fast", ctx.signal);
			pi.events.emit(VALIDATION_RESULT_EVENT, result);

			if (result.passed) {
				lastFailureFingerprint = undefined;
				automaticRepairRounds = 0;
				return;
			}

			if (result.fingerprint === lastFailureFingerprint) return;
			lastFailureFingerprint = result.fingerprint;
			if (automaticRepairRounds >= MAX_AUTOMATIC_REPAIR_ROUNDS) {
				ctx.ui.notify("Automatic validation still fails; repair limit reached.", "error");
				return;
			}

			automaticRepairRounds++;
			pi.sendMessage(
				{
					customType: "validation-feedback",
					content: [
						"Automatic changed-file validation failed.",
						`Repair round ${automaticRepairRounds}/${MAX_AUTOMATIC_REPAIR_ROUNDS}.`,
						"Fix only failures caused by the current task, then verify again.",
						"",
						formatValidationResult(result),
					].join("\n"),
					display: true,
					details: result,
				},
				{ deliverAs: "followUp", triggerTurn: true },
			);
		} finally {
			checking = false;
		}
	});
}
