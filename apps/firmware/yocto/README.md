# Yocto

`kas/firmware.yml` pins the Yocto layers. `meta-firmware` contains the firmware
package and flashable image recipes. Build it from the repository root with
`just --justfile apps/firmware/justfile image`.

The development container includes `kas` and the Yocto host tools. After changing
`yocto/Cargo.lock`, regenerate `firmware-crates.inc` without nested Docker:
`just --justfile apps/firmware/justfile update-crates`. This runs Yocto's
`cargo-update-recipe-crates` task; do not edit the generated crate list manually.
