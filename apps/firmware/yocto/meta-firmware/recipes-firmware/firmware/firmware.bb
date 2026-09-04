SUMMARY = "Raspberry Pi firmware"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE;md5=f82d4c65d86894b2184ce118b8779401"

inherit cargo externalsrc systemd

# cargo.bbclass builds offline, so every crates.io package needed by firmware
# must be available through BitBake's crate fetcher.
SRC_URI += " \
    crate://crates.io/spin/0.12.3 \
"

FIRMWARE_SOURCE_DIR ??= "${TOPDIR}/../.."
EXTERNALSRC = "${FIRMWARE_SOURCE_DIR}"
EXTERNALSRC_BUILD = "${WORKDIR}/build"
SOURCE_BASEDIR = "${EXTERNALSRC}/apps/firmware"
CARGO_MANIFEST_PATH = "${SOURCE_BASEDIR}/Cargo.toml"

# base_do_unpack resets SOURCE_BASEDIR to EXTERNALSRC when a recipe combines an
# external tree with fetched crates. Restore the narrow source directory before
# reproducible.py scans it; scanning the whole checkout races rm_work through
# the CI-mounted .cache/yocto tree.
python firmware_limit_source_date_epoch_scan() {
    d.setVar("SOURCE_BASEDIR", d.getVar("EXTERNALSRC") + "/apps/firmware")
}
do_unpack[postfuncs]:prepend = "firmware_limit_source_date_epoch_scan "

FIRMWARE_FILES_DIR := "${THISDIR}/files"

SYSTEMD_SERVICE:${PN} = "firmware.service"
SYSTEMD_AUTO_ENABLE:${PN} = "enable"

do_install[file-checksums] += "${FIRMWARE_FILES_DIR}/firmware.service:True"

do_install:append() {
    install -d "${D}${systemd_system_unitdir}"
    install -m 0644 "${FIRMWARE_FILES_DIR}/firmware.service" \
        "${D}${systemd_system_unitdir}/firmware.service"
}

SRC_URI[spin-0.12.3.sha256sum] = "0134f9043ed38b087ac4f7d4af44c79e2c9e5094421fe3164f435ce585953b10"
