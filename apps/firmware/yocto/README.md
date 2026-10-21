# Yocto

| Path | Purpose |
| --- | --- |
| `kas/firmware.yml` | Pinned Yocto layers and build configuration |
| `meta-firmware/` | Firmware package and flashable image recipes |
| `Cargo.toml`, `Cargo.lock` | Isolated manifest so BitBake resolves only the firmware graph |
| `cache.sh` | Saves and restores the build cache in an OCI registry |

Build the image from the repository root:

```sh
just --justfile apps/firmware/justfile image
```

## Crate metadata

BitBake fetches crates offline from the list in `firmware-crates.inc`, which is
generated. After changing `yocto/Cargo.lock`, regenerate it inside the
development container (no nested Docker needed):

```sh
just --justfile apps/firmware/justfile update-crates
```

## Build caching

Local builds reuse `.cache/yocto/downloads` and `.cache/yocto/sstate-cache`.

CI stores the same directories in `ghcr.io/<owner>/<repo>/yocto-cache` using
`GITHUB_TOKEN`; no extra secret is needed.
[GHCR storage and bandwidth are currently free](https://docs.github.com/en/billing/concepts/product-billing/github-packages)
and do not expire like the Actions cache.

`cache.sh` (GNU tar, split and ORAS 1.3.4) keeps three tags:

- `v1-linux-amd64-toolchain`: compilers and native tools, which rarely change.
- `v1-linux-amd64-system`: the rest of sstate.
- `v1-linux-amd64-sources`: downloads.

Archives are sorted, with normalized timestamps, ownership and permissions,
and split into 1 GiB parts. The registry reuses unchanged parts, so an
application change does not re-upload the toolchain. Fresh runners still
download and unpack all three groups.

CI behavior:

- Only `main` updates the shared cache, and main builds run one at a time.
- Cache failures never fail the build.
- The image step is limited to four hours. Any remaining build container is
  then stopped and the completed tasks are saved, even after a failure. A
  timed-out build still fails and publishes no image; the next main run reuses
  its completed tasks.
- Step limits add up to less than the six-hour job limit, leaving up to 45
  minutes for the cache upload.
- Cleanup keeps the three tags and the six most recent untagged versions;
  files inside the tagged snapshots are never pruned by age.
- If the registry cache is missing or cannot be restored, the build compiles
  from scratch.

CI image build times have not been measured yet.

With ORAS installed and authenticated, run the same operations locally:

```sh
just --justfile apps/firmware/justfile cache-restore ghcr.io/<owner>/<repo>/yocto-cache
just --justfile apps/firmware/justfile cache-save ghcr.io/<owner>/<repo>/yocto-cache
```
