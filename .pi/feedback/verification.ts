import { createHash } from "node:crypto";
import { mkdir, readFile, stat, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";
import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { truncateTail } from "@earendil-works/pi-coding-agent";
import { pathsFromNameStatus, splitNull } from "./git-paths.js";

export type ValidationLevel = "fast" | "test" | "full";

export interface CheckResult {
	id: string;
	command: string;
	code: number;
	durationMs: number;
	output: string;
	fullOutputPath?: string;
}

export interface ValidationResult {
	level: ValidationLevel;
	paths: string[];
	passed: boolean;
	checks: CheckResult[];
	fingerprint: string;
}

interface CheckSpec {
	id: string;
	command: string;
	args: string[];
	timeoutMs?: number;
}

const RUST_PACKAGES = new Map([
	["apps/firmware", "firmware"],
	["apps/simulator", "chess-simulator"],
	["crates/chess", "chess"],
	["crates/core", "chess-core"],
	["crates/logger", "logger"],
	["crates/menu", "menu"],
	["crates/persistence", "persistence"],
]);

const PYTHON_PACKAGES = ["hardware/shared", "hardware/cad", "hardware/pcb"] as const;
const PI_HARNESS_PATHS = [".pi", ".github", ".devcontainer"] as const;
const WORKSPACE_ROOT = "<workspace>";
const YOCTO_METADATA_EXTENSIONS = [".bb", ".bbappend", ".conf", ".inc", ".yaml", ".yml"] as const;
const MAX_RESULT_LINES = 160;
const MAX_RESULT_BYTES = 16 * 1024;
const CHECK_TIMEOUT_MS = 2 * 60 * 1000;
const YOCTO_CHECK_TIMEOUT_MS = 15 * 60 * 1000;

export async function getDirtyPaths(pi: ExtensionAPI, cwd: string): Promise<string[]> {
	const tracked = await pi.exec("git", ["-C", cwd, "diff", "--name-status", "-z", "HEAD", "--"]);
	if (tracked.code !== 0) return [];

	const untracked = await pi.exec("git", [
		"-C",
		cwd,
		"ls-files",
		"--others",
		"--exclude-standard",
		"-z",
		"--",
	]);
	if (untracked.code !== 0) return [];

	return [...new Set([...pathsFromNameStatus(tracked.stdout), ...splitNull(untracked.stdout)])].sort();
}

export async function snapshotDirtyFiles(pi: ExtensionAPI, cwd: string): Promise<Map<string, string>> {
	const snapshot = new Map<string, string>();
	for (const path of await getDirtyPaths(pi, cwd)) {
		const absolutePath = resolve(cwd, path);
		try {
			const metadata = await stat(absolutePath);
			if (!metadata.isFile()) {
				snapshot.set(path, `other:${metadata.mode}:${metadata.size}`);
				continue;
			}
			const content = await readFile(absolutePath);
			snapshot.set(path, createHash("sha256").update(content).digest("hex"));
		} catch {
			snapshot.set(path, "missing");
		}
	}
	return snapshot;
}

export function changedPaths(before: Map<string, string>, after: Map<string, string>): string[] {
	const paths = new Set([...before.keys(), ...after.keys()]);
	return [...paths].filter((path) => before.get(path) !== after.get(path)).sort();
}

function quote(value: string): string {
	return /^[A-Za-z0-9_./:=+-]+$/.test(value) ? value : JSON.stringify(value);
}

function displayCommand(command: string, args: string[]): string {
	return [command, ...args].map(quote).join(" ");
}

function diffCheck(cwd: string, paths: string[], baseRevision?: string): CheckSpec {
	return {
		id: "repository:diff-check",
		command: "git",
		args: [
			"-C",
			cwd,
			"diff",
			"--check",
			...(baseRevision ? [baseRevision] : []),
			...(paths.length > 0 ? ["--", ...paths] : []),
		],
	};
}

function validationRoot(path: string): string | undefined {
	if (path === "Cargo.toml" || path === "Cargo.lock") return WORKSPACE_ROOT;
	if (PI_HARNESS_PATHS.some((root) => path === root || path.startsWith(`${root}/`))) return ".pi";
	return [...RUST_PACKAGES.keys(), ...PYTHON_PACKAGES]
		.find((root) => path === root || path.startsWith(`${root}/`));
}

function packageRoots(paths: string[]): string[] {
	return [...new Set(paths.map(validationRoot).filter((root): root is string => root !== undefined))].sort();
}

function isYoctoMetadata(path: string): boolean {
	return path.startsWith("apps/firmware/yocto/")
		&& YOCTO_METADATA_EXTENSIONS.some((extension) => path.endsWith(extension));
}

function yoctoMetadataCheck(cwd: string): CheckSpec {
	return {
		id: "apps/firmware:image-check",
		command: "just",
		args: ["--justfile", join(cwd, "apps/firmware/justfile"), "image-check"],
		timeoutMs: YOCTO_CHECK_TIMEOUT_MS,
	};
}

export function selectChecks(cwd: string, paths: string[], level: ValidationLevel, baseRevision?: string): CheckSpec[] {
	const roots = packageRoots(paths);
	const yoctoMetadataPaths = paths.filter(isYoctoMetadata);
	const firmwareCodePaths = paths.filter((path) => path.startsWith("apps/firmware/") && !isYoctoMetadata(path));
	const hasUnscopedPaths = paths.some((path) => validationRoot(path) === undefined);

	if (paths.length === 0) {
		if (level === "fast") {
			return [diffCheck(cwd, paths, baseRevision)];
		}
		const recipe = level === "full" ? "precommit" : "test";
		return [{ id: `repository:${recipe}`, command: "just", args: ["--justfile", join(cwd, "justfile"), recipe] }];
	}

	const checks: CheckSpec[] = roots.map((root) => {
		if (root === WORKSPACE_ROOT) {
			if (level !== "fast") {
				const recipe = level === "test" ? "test" : "precommit";
				return {
					id: `repository:${recipe}`,
					command: "just",
					args: ["--justfile", join(cwd, "justfile"), recipe],
				};
			}
			return {
				id: "workspace:cargo-check",
				command: "cargo",
				args: [
					"check",
					"--manifest-path",
					join(cwd, "Cargo.toml"),
					"--workspace",
					"--all-targets",
					"--all-features",
				],
			};
		}

		if (root === ".pi") {
			return {
				id: ".pi:check",
				command: "bun",
				args: ["run", "--cwd", join(cwd, ".pi"), "check"],
			};
		}

		const firmwareYoctoPaths = root === "apps/firmware"
			? paths.filter((path) => path.startsWith("apps/firmware/yocto/"))
			: [];
		if (root === "apps/firmware" && yoctoMetadataPaths.length > 0 && firmwareCodePaths.length === 0) {
			return yoctoMetadataCheck(cwd);
		}

		if (level === "fast" && RUST_PACKAGES.has(root) && firmwareYoctoPaths.length === 0) {
			const packageName = RUST_PACKAGES.get(root)!;
			const args = [
				"check",
				"--manifest-path",
				join(cwd, "Cargo.toml"),
				"--package",
				packageName,
				"--all-targets",
				"--all-features",
			];
			return { id: `${root}:cargo-check`, command: "cargo", args };
		}

		const recipe = level === "fast" ? "quality" : level === "test" ? "test" : root === "hardware/pcb" ? "check-fast" : "check";
		return {
			id: `${root}:${recipe}`,
			command: "just",
			args: ["--justfile", join(cwd, root, "justfile"), recipe],
		};
	});
	if (yoctoMetadataPaths.length > 0 && firmwareCodePaths.length > 0) {
		checks.push(yoctoMetadataCheck(cwd));
	}
	const harnessShellPaths = paths.filter((path) =>
		path === ".githooks/pre-commit"
		|| (path.endsWith(".sh") && (path.startsWith(".devcontainer/") || path.startsWith(".github/")))
	);
	for (const path of [...new Set(harnessShellPaths)].sort()) {
		const absolutePath = join(cwd, path);
		checks.push({
			id: `${path}:bash-syntax`,
			command: "bash",
			args: ["-c", '[[ ! -e "$1" ]] || bash -n "$1"', "--", absolutePath],
		});
	}
	if (level === "full" && !checks.some((check) => check.id === "repository:precommit")) {
		checks.push({
			id: "repository:precommit",
			command: "just",
			args: ["--justfile", join(cwd, "justfile"), "precommit"],
		});
	} else if (hasUnscopedPaths && level === "fast") {
		checks.push(diffCheck(cwd, paths, baseRevision));
	} else if (hasUnscopedPaths) {
		checks.push({
			id: "repository:test",
			command: "just",
			args: ["--justfile", join(cwd, "justfile"), "test"],
		});
	}
	return checks;
}

export async function preparePiDependencies(
	pi: ExtensionAPI,
	cwd: string,
	paths: string[],
	signal?: AbortSignal,
): Promise<void> {
	const needsPiDependencies = selectChecks(cwd, paths, "fast").some((check) => check.id === ".pi:check");
	if (!needsPiDependencies) return;

	const result = await pi.exec(
		"bun",
		["install", "--cwd", join(cwd, ".pi"), "--frozen-lockfile"],
		{ signal, timeout: CHECK_TIMEOUT_MS },
	);
	if (result.code !== 0) {
		const output = [result.stdout, result.stderr].filter(Boolean).join("\n").trim();
		throw new Error(`Could not install Pi dependencies in the validation snapshot: ${output || `exit ${result.code}`}`);
	}
}

export async function runVerification(
	pi: ExtensionAPI,
	cwd: string,
	paths: string[],
	level: ValidationLevel,
	signal?: AbortSignal,
	baseRevision?: string,
): Promise<ValidationResult> {
	const checks: CheckResult[] = [];
	for (const spec of selectChecks(cwd, paths, level, baseRevision)) {
		const startedAt = Date.now();
		const execution = await pi.exec(spec.command, spec.args, {
			signal,
			timeout: spec.timeoutMs ?? CHECK_TIMEOUT_MS,
		});
		const completeOutput = [execution.stdout, execution.stderr].filter(Boolean).join("\n").trim();
		const truncation = truncateTail(completeOutput || "(no output)", {
			maxLines: MAX_RESULT_LINES,
			maxBytes: MAX_RESULT_BYTES,
		});
		let fullOutputPath: string | undefined;

		if (truncation.truncated) {
			const logDirectory = join(tmpdir(), "pi-validation-feedback");
			await mkdir(logDirectory, { recursive: true });
			fullOutputPath = join(logDirectory, `${Date.now()}-${spec.id.replace(/[^a-z0-9_.-]+/gi, "-")}.log`);
			await writeFile(fullOutputPath, completeOutput, "utf8");
		}

		checks.push({
			id: spec.id,
			command: displayCommand(spec.command, spec.args),
			code: execution.code,
			durationMs: Date.now() - startedAt,
			output: truncation.content,
			fullOutputPath,
		});

		if (execution.code !== 0) break;
	}

	const fingerprint = createHash("sha256")
		.update(checks.map((check) => `${check.id}\0${check.code}\0${check.output}`).join("\0"))
		.digest("hex");

	return {
		level,
		paths: [...paths].sort(),
		passed: checks.every((check) => check.code === 0),
		checks,
		fingerprint,
	};
}

export function formatValidationResult(result: ValidationResult): string {
	const heading = result.passed ? "Validation passed." : "Validation failed.";
	const lines = [heading, `Level: ${result.level}`, `Paths: ${result.paths.join(", ") || "all dirty paths"}`];

	for (const check of result.checks) {
		lines.push("", `Command: ${check.command}`, `Exit code: ${check.code}`, check.output);
		if (check.fullOutputPath) lines.push(`Full output: ${check.fullOutputPath}`);
	}
	return lines.join("\n");
}
