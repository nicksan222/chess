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
config="${repository_root}/.devcontainer/ci.json"

python3 - "${config}" "${image}" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
image = sys.argv[2]
path.write_text(
    json.dumps(
        {
            "name": "Chess CI",
            "image": image,
            "remoteUser": "vscode",
            "updateRemoteUserUID": True,
            "containerEnv": {"RUST_BACKTRACE": "1"},
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
