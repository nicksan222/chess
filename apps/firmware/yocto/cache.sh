#!/usr/bin/env bash
# Save or restore the Yocto build cache as OCI artifacts in a registry.
#
# Usage: cache.sh restore|save REGISTRY [GROUP]
#
# The cache is split into three groups, each pushed to its own tag:
#   toolchain  sstate of compilers and native tools, which rarely changes
#   system     every other sstate archive
#   sources    fetched downloads
# Archives are deterministic and split into fixed-size parts, so the registry
# reuses every part whose content did not change.
#
# Environment:
#   YOCTO_CACHE_DIR         cache directory (default: .cache/yocto)
#   YOCTO_CACHE_PART_SIZE   size of each archive part (default: 1G)
#   YOCTO_CACHE_PLAIN_HTTP  set to 1 for a registry without TLS
set -euo pipefail

usage() {
  echo "usage: cache.sh restore|save REGISTRY [GROUP]" >&2
  exit 2
}

[[ $# == 2 || $# == 3 ]] || usage
operation="$1"
registry="${2,,}" # OCI references must be lowercase.
group="${3:-}"

case "$operation" in restore | save) ;; *) usage ;; esac
case "$group" in toolchain | system | sources | "") ;; *) usage ;; esac

# Without a group, handle each group in its own process: errexit is ignored
# inside `command || ...`, and one failing group must not stop the others.
if [[ -z $group ]]; then
  status=0
  for group in toolchain system sources; do
    bash "$0" "$operation" "$registry" "$group" || status=1
  done
  exit "$status"
fi

mkdir -p "${YOCTO_CACHE_DIR:-.cache/yocto}"
cache="$(realpath "${YOCTO_CACHE_DIR:-.cache/yocto}")"
work="$(mktemp -d "$cache/registry.XXXXXX")"
trap 'rm -rf -- "$work"' EXIT

reference="$registry:v1-linux-amd64-$group"
oras_options=()
if [[ ${YOCTO_CACHE_PLAIN_HTTP:-0} == 1 ]]; then
  oras_options+=(--plain-http)
fi

# Succeed if an sstate archive belongs to the toolchain group.
is_toolchain() {
  case "${1##*/}" in
    sstate:*-native:* | sstate:*-cross-*:*) ;;
    sstate:gcc*:* | sstate:libgcc*:* | sstate:binutils*:*) ;;
    sstate:llvm*:* | sstate:clang*:*) ;;
    sstate:rust*:* | sstate:cargo*:* | sstate:libstd-rs*:*) ;;
    *) return 1 ;;
  esac
}

# Print the group's completed cache entries, NUL-separated, relative to $cache.
list_group() {
  local file kind
  if [[ $group == sources ]]; then
    [[ -d downloads ]] || return 0
    find downloads ! -name '*.lock' ! -name '*.tmp' -print0
    return
  fi

  [[ -d sstate-cache ]] || return 0
  find sstate-cache -type f -name 'sstate:*' ! -name '*.lock' ! -name '*.tmp' -print0 |
    while IFS= read -r -d '' file; do
      if is_toolchain "$file"; then kind=toolchain; else kind=system; fi
      if [[ $kind == "$group" ]]; then printf '%s\0' "$file"; fi
    done
}

restore() {
  local digest
  digest="$(oras resolve "${oras_options[@]}" "$reference")"
  oras pull "${oras_options[@]}" "$registry@$digest" --output "$work"
  cat "$work"/cache.part-* | tar --extract --file=- --directory="$cache" --no-same-owner
}

save() {
  cd "$cache"
  list_group | sort -z > "$work/files"
  if [[ ! -s $work/files ]]; then
    echo "No completed $group cache files to save"
    return
  fi

  # Fixed order, timestamps, owners and modes make identical input produce
  # identical parts.
  tar --create --file=- --no-recursion --null --files-from="$work/files" \
    --mtime=@0 --owner=0 --group=0 --numeric-owner --mode=a=rX,u+w |
    split --bytes="${YOCTO_CACHE_PART_SIZE:-1G}" --numeric-suffixes --suffix-length=4 \
      - "$work/cache.part-"

  cd "$work"
  oras push "${oras_options[@]}" "$reference" \
    --artifact-type application/vnd.chess.yocto-cache.v1 \
    --annotation "org.opencontainers.image.source=https://github.com/${GITHUB_REPOSITORY:-nicksan222/chess}" \
    --annotation org.opencontainers.image.created=1970-01-01T00:00:00Z \
    cache.part-*
}

"$operation"
