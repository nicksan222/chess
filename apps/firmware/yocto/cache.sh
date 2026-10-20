#!/usr/bin/env bash
# Three deterministic cache archives, stored as reusable OCI blobs in GHCR.
set -euo pipefail

operation="${1:?usage: cache.sh restore|save registry}"
registry="${2,,}"
case "$operation" in restore|save) ;; *) exit 2 ;; esac

# Separate processes keep errexit effective even when another group fails.
if [[ $# == 2 ]]; then
  status=0
  for group in toolchain system sources; do
    bash "$0" "$operation" "$registry" "$group" || status=1
  done
  exit "$status"
fi
group="$3"
cache="${YOCTO_CACHE_DIR:-.cache/yocto}"
mkdir -p "$cache"
cache="$(realpath "$cache")"
work="$(mktemp -d "$cache/registry.XXXXXX")"
trap 'rm -rf -- "$work"' EXIT
reference="$registry:v1-linux-amd64-$group"
options=()
if [[ ${YOCTO_CACHE_PLAIN_HTTP:-0} == 1 ]]; then
  options+=(--plain-http)
fi

if [[ $operation == restore ]]; then
  digest="$(oras resolve "${options[@]}" "$reference")"
  oras pull "${options[@]}" "$registry@$digest" --output "$work"
  cat "$work"/cache.part-* | tar -xf - -C "$cache" --no-same-owner
  exit
fi

cd "$cache"
if [[ $group == sources ]]; then
  if [[ -d downloads ]]; then
    find downloads ! -name '*.lock' ! -name '*.tmp' -print0 > "$work/files"
  fi
elif [[ -d sstate-cache ]]; then
  while IFS= read -r -d '' file; do
    case "${file##*/}" in
      sstate:*-native:*|sstate:*-cross-*:*|sstate:rust*:*|sstate:llvm*:*|sstate:clang*:*|sstate:cargo*:*|sstate:gcc*:*|sstate:binutils*:*|sstate:libgcc*:*|sstate:libstd-rs*:*) kind=toolchain ;;
      *) kind=system ;;
    esac
    if [[ $kind == "$group" ]]; then
      printf '%s\0' "$file"
    fi
  done < <(find sstate-cache -type f -name 'sstate:*' ! -name '*.lock' ! -name '*.tmp' -print0) > "$work/files"
fi
if [[ ! -s $work/files ]]; then
  echo "No completed $group cache files to save"
  exit
fi

sort -z "$work/files" > "$work/sorted"
tar --create --file=- --mtime=@0 --owner=0 --group=0 --numeric-owner \
  --mode=a=rX,u+w --no-recursion --null --files-from="$work/sorted" \
  | split --bytes="${YOCTO_CACHE_PART_SIZE:-1G}" --numeric-suffixes --suffix-length=4 - "$work/cache.part-"
cd "$work"
oras push "${options[@]}" "$reference" \
  --artifact-type application/vnd.chess.yocto-cache.v1 \
  --annotation "org.opencontainers.image.source=https://github.com/${GITHUB_REPOSITORY:-nicksan222/chess}" \
  --annotation org.opencontainers.image.created=1970-01-01T00:00:00Z \
  cache.part-*
