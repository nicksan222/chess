SUMMARY = "Raspberry Pi firmware"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE;md5=f82d4c65d86894b2184ce118b8779401"

inherit cargo externalsrc systemd

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
