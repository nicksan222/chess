SUMMARY = "Raspberry Pi firmware"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE;md5=f82d4c65d86894b2184ce118b8779401"

inherit cargo externalsrc systemd

# cargo.bbclass builds offline, so every crates.io package in the workspace
# lockfile must be available through BitBake's crate fetcher.
SRC_URI += " \
    crate://crates.io/block-buffer/0.10.4 \
    crate://crates.io/cfg-if/1.0.4 \
    crate://crates.io/cpufeatures/0.2.17 \
    crate://crates.io/crypto-common/0.1.7 \
    crate://crates.io/digest/0.10.7 \
    crate://crates.io/generic-array/0.14.7 \
    crate://crates.io/libc/0.2.189 \
    crate://crates.io/sha2/0.10.9 \
    crate://crates.io/typenum/1.20.1 \
    crate://crates.io/version_check/0.9.5 \
"

FIRMWARE_SOURCE_DIR ??= "${TOPDIR}/../.."
EXTERNALSRC = "${FIRMWARE_SOURCE_DIR}"
EXTERNALSRC_BUILD = "${WORKDIR}/build"
SOURCE_BASEDIR = "${EXTERNALSRC}/apps/firmware"
CARGO_MANIFEST_PATH = "${SOURCE_BASEDIR}/Cargo.toml"

FIRMWARE_FILES_DIR := "${THISDIR}/files"

SYSTEMD_SERVICE:${PN} = "firmware.service"
SYSTEMD_AUTO_ENABLE:${PN} = "enable"

do_install[file-checksums] += "${FIRMWARE_FILES_DIR}/firmware.service:True"

do_install:append() {
    install -d "${D}${systemd_system_unitdir}"
    install -m 0644 "${FIRMWARE_FILES_DIR}/firmware.service" \
        "${D}${systemd_system_unitdir}/firmware.service"
}
