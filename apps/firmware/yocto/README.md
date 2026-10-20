# Yocto

`kas/firmware.yml` pins the Yocto layers. `meta-firmware` contains the firmware
package and flashable image recipes. Build it from the repository root with
`just --justfile apps/firmware/justfile image`.

The development container includes `kas` and the Yocto host tools. After changing
`yocto/Cargo.lock`, regenerate `firmware-crates.inc` without nested Docker:
`just --justfile apps/firmware/justfile update-crates`. This runs Yocto's
`cargo-update-recipe-crates` task; do not edit the generated crate list manually.

## Build caching

Local builds reuse `.cache/yocto/downloads` and `.cache/yocto/sstate-cache`.
CI stores them in `ghcr.io/<owner>/<repo>/yocto-cache`, using `GITHUB_TOKEN`.
[GHCR storage and bandwidth are currently free](https://docs.github.com/en/billing/concepts/product-billing/github-packages)
and separate from Actions cache storage and idle expiry. No paid storage setting
or extra secret is needed.

`cache.sh` uses GNU tar, split, and ORAS 1.3.4 to maintain three tags:
`v1-linux-amd64-toolchain`, `v1-linux-amd64-system`, and `v1-linux-amd64-sources`.
Sorted archives have normalized timestamps, ownership and permissions and are
split into 1 GiB blobs. GHCR reuses identical blobs. A changed group can upload
multiple chunks again, but application changes leave the toolchain group alone.
Fresh runners still download and unpack all three groups.

Only main builds update the shared cache. Cache failures are non-fatal; completed
tasks are saved after failed builds too. CI limits the image step to four hours,
then stops any remaining build container before archiving the cache. All step
budgets together stay below the six-hour job limit, reserving up to 45 minutes
for cache uploads. A timed-out build remains a failure and publishes no image;
the next main run can reuse its completed tasks. Main builds run sequentially,
preserving in-progress compilation. Cleanup retains the three tagged snapshots and six
recent untagged versions. Files inside active snapshots are not age-pruned.
The old Actions archive is a migration fallback and is no longer written.
The first run seeds GHCR; cold compilation remains necessary if neither cache is
available. Image build times still need measurement on CI.

With ORAS installed and authenticated, the same operations are available locally:

```sh
just --justfile apps/firmware/justfile cache-restore ghcr.io/<owner>/<repo>/yocto-cache
just --justfile apps/firmware/justfile cache-save ghcr.io/<owner>/<repo>/yocto-cache
```
