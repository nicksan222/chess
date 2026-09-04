const PATTERNS = [
	/[a-z0-9_-]*(?:api[-_]?key|secret|password|token)[a-z0-9_-]*["']?\s*[:=]\s*["'][^"']{8,}/i,
	/^\+\s*(?:export\s+)?["']?[a-z0-9_-]*(?:api[-_]?key|secret|password|token)[a-z0-9_-]*["']?\s*[:=]\s*[^\s#"']{8,}\s*(?:#.*)?$/i,
	/-----BEGIN (?:[A-Z0-9]+ )*PRIVATE KEY-----/,
	/ghp_[A-Za-z0-9]{20,}/,
	/github_pat_[A-Za-z0-9_]{20,}/,
	/sk-[A-Za-z0-9_-]{20,}/,
];

export function suspiciousTextLines(text: string): string[] {
	return text
		.split("\n")
		.filter((line) => PATTERNS.some((pattern) => pattern.test(line) || pattern.test(`+${line}`)))
		.slice(0, 5);
}

export function suspiciousPatchLines(patch: string): string[] {
	return suspiciousTextLines(
		patch
			.split("\n")
			.filter((line) => line.startsWith("+") && !line.startsWith("+++"))
			.join("\n"),
	);
}
