export function suspiciousPatchLines(patch: string): string[] {
	const patterns = [
		/[a-z0-9_-]*(?:api[-_]?key|secret|password|token)[a-z0-9_-]*["']?\s*[:=]\s*["'][^"']{8,}/i,
		/^\+\s*(?:export\s+)?["']?[a-z0-9_-]*(?:api[-_]?key|secret|password|token)[a-z0-9_-]*["']?\s*[:=]\s*[^\s#"']{8,}\s*(?:#.*)?$/i,
		/-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----/,
		/ghp_[A-Za-z0-9]{20,}/,
		/github_pat_[A-Za-z0-9_]{20,}/,
		/sk-[A-Za-z0-9_-]{20,}/,
	];
	return patch
		.split("\n")
		.filter((line) => line.startsWith("+") && !line.startsWith("+++"))
		.filter((line) => patterns.some((pattern) => pattern.test(line)))
		.slice(0, 5);
}
