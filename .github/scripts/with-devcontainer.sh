#!/usr/bin/env bash
set -euo pipefail

# Start the prebuilt development image with the Dev Container CLI and run one
# command. Used by CI after the prebuild job; DEVCONTAINER_IMAGE is required.

repository_root="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "${repository_root}"

if [[ $# -eq 0 ]]; then
    printf 'Usage: with-devcontainer.sh <command> [args...]\n' >&2
    exit 2
fi

image="${DEVCONTAINER_IMAGE:?DEVCONTAINER_IMAGE is not set}"
config_dir="$(mktemp -d "${TMPDIR:-/tmp}/chess-devcontainer.XXXXXX")"
config="${config_dir}/devcontainer.json"

python3 - "${config}" "${image}" "${GITHUB_RUN_ID:-}" "${GITHUB_SERVER_URL:-}" <<'PY'
import json
import os
import sys
from pathlib import Path

path = Path(sys.argv[1])
image = sys.argv[2]
run_id = sys.argv[3] if len(sys.argv) > 3 else ""
server_url = sys.argv[4] if len(sys.argv) > 4 else ""

container_env = {"RUST_BACKTRACE": "1"}
if run_id:
    container_env["GITHUB_RUN_ID"] = run_id
if server_url:
    container_env["GITHUB_SERVER_URL"] = server_url

path.write_text(
    json.dumps(
        {
            "name": "Chess CI",
            "image": image,
            "remoteUser": "vscode",
            "updateRemoteUserUID": True,
            "containerEnv": container_env,
        },
        indent=2,
    )
    + "\n"
)
PY

docker pull "${image}"
devcontainer up \
    --workspace-folder "${repository_root}" \
    --config "${config}" \
    --skip-post-create
devcontainer exec \
    --workspace-folder "${repository_root}" \
    --config "${config}" \
    "$@"
