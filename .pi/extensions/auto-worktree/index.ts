import { existsSync, mkdirSync, writeFileSync } from "node:fs";
import { homedir } from "node:os";
import { basename, join, resolve } from "node:path";
import { SessionManager, type ExtensionAPI, type ExtensionCommandContext } from "@earendil-works/pi-coding-agent";

const BOOTSTRAP_COMMAND = "auto-worktree-bootstrap";
const ACTIVE_ENV = "PI_AUTO_WORKTREE_ACTIVE";
const DISABLE_ENV = "PI_AUTO_WORKTREE_DISABLE";

function configuredRoot(): string {
	const configured = process.env.PI_AUTO_WORKTREE_ROOT?.trim();
	if (!configured) return join(homedir(), ".worktrees");
	if (configured === "~") return homedir();
	if (configured.startsWith("~/")) return join(homedir(), configured.slice(2));
	return resolve(configured);
}

async function git(pi: ExtensionAPI, cwd: string, args: string[]) {
	return pi.exec("git", ["-C", cwd, ...args]);
}

function createTargetSession(ctx: ExtensionCommandContext, targetPath: string): string {
	const sourceFile = ctx.sessionManager.getSessionFile();
	if (sourceFile && existsSync(sourceFile)) {
		const target = SessionManager.forkFrom(sourceFile, targetPath);
		const targetFile = target.getSessionFile();
		if (!targetFile) throw new Error("Pi did not create a target worktree session.");
		return targetFile;
	}

	if (ctx.sessionManager.getEntries().length !== 0) {
		throw new Error("Cannot automatically move a non-persisted conversation into a worktree.");
	}

	const target = SessionManager.create(targetPath);
	const targetFile = target.getSessionFile();
	const header = target.getHeader();
	if (!targetFile || !header) throw new Error("Pi did not prepare an empty target session.");
	writeFileSync(targetFile, `${JSON.stringify(header)}\n`, { encoding: "utf8", flag: "wx", mode: 0o600 });
	return targetFile;
}

async function bootstrap(pi: ExtensionAPI, ctx: ExtensionCommandContext): Promise<void> {
	await ctx.waitForIdle();
	const topLevel = await git(pi, ctx.cwd, ["rev-parse", "--show-toplevel"]);
	if (topLevel.code !== 0) throw new Error("The current Pi workspace is not a Git worktree.");
	const repository = topLevel.stdout.trim();
	const head = await git(pi, ctx.cwd, ["rev-parse", "HEAD"]);
	if (head.code !== 0) throw new Error("The current Git HEAD cannot be resolved.");

	const sessionId = ctx.sessionManager.getSessionId();
	const token = sessionId.replace(/[^a-zA-Z0-9-]/g, "-");
	const branch = `pi/${token}`;
	const parent = join(configuredRoot(), basename(repository));
	const targetPath = join(parent, `pi-${token}`);
	if (existsSync(targetPath)) throw new Error(`Automatic worktree path already exists: ${targetPath}`);

	const branchExists = await git(pi, repository, ["show-ref", "--verify", "--quiet", `refs/heads/${branch}`]);
	if (branchExists.code === 0) throw new Error(`Automatic worktree branch already exists: ${branch}`);
	mkdirSync(parent, { recursive: true });

	ctx.ui.notify(`Creating isolated worktree ${targetPath}…`, "info");
	const added = await git(pi, repository, ["worktree", "add", "-b", branch, targetPath, head.stdout.trim()]);
	if (added.code !== 0) {
		throw new Error([added.stderr, added.stdout].filter(Boolean).join("\n").trim() || "git worktree add failed");
	}

	let targetSession: string;
	try {
		targetSession = createTargetSession(ctx, targetPath);
	} catch (error) {
		throw new Error(`Worktree retained at ${targetPath}, but Pi session creation failed: ${error instanceof Error ? error.message : String(error)}`);
	}

	const switched = await ctx.switchSession(targetSession, {
		withSession: async (replacementContext) => {
			replacementContext.ui.notify(`Pi is isolated in ${targetPath} on ${branch}.`, "info");
		},
	});
	if (switched.cancelled) throw new Error(`Workspace switch was cancelled; worktree retained at ${targetPath}.`);
}

export default function autoWorktree(pi: ExtensionAPI) {
	let bootstrapQueued = false;

	pi.registerCommand(BOOTSTRAP_COMMAND, {
		description: "Internal command that moves a new Pi process into its own Git worktree",
		handler: async (_args, ctx) => {
			try {
				await bootstrap(pi, ctx);
			} catch (error) {
				delete process.env[ACTIVE_ENV];
				ctx.ui.notify(`Automatic worktree setup failed: ${error instanceof Error ? error.message : String(error)}`, "error");
			}
		},
	});

	pi.on("session_start", (event, ctx) => {
		if (
			event.reason !== "startup" ||
			bootstrapQueued ||
			process.env[ACTIVE_ENV] ||
			process.env[DISABLE_ENV] === "1"
		) {
			return;
		}
		bootstrapQueued = true;
		process.env[ACTIVE_ENV] = ctx.sessionManager.getSessionId();
		queueMicrotask(() => {
			try {
				pi.sendUserMessage(`/${BOOTSTRAP_COMMAND}`, { expandPromptTemplates: true });
			} catch (error) {
				delete process.env[ACTIVE_ENV];
				ctx.ui.notify(`Could not queue automatic worktree setup: ${error instanceof Error ? error.message : String(error)}`, "error");
			}
		});
	});
}
