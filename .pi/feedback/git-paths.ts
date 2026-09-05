export function splitNull(value: string): string[] {
	return value.split("\0").filter((item) => item.length > 0);
}

export function pathsFromNameStatus(value: string): string[] {
	const fields = splitNull(value);
	const paths: string[] = [];
	for (let index = 0; index < fields.length;) {
		const status = fields[index++];
		if (!status) break;
		const firstPath = fields[index++];
		if (firstPath) paths.push(firstPath);
		if (status.startsWith("R") || status.startsWith("C")) {
			const secondPath = fields[index++];
			if (secondPath) paths.push(secondPath);
		}
	}
	return [...new Set(paths)].sort();
}
