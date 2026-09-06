SUMMARY = "Raspberry Pi firmware"
LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE;md5=f82d4c65d86894b2184ce118b8779401"

inherit cargo externalsrc systemd

# cargo.bbclass builds the isolated Yocto manifest offline, so each package in
# its small lockfile must be available through BitBake's crate fetcher.
SRC_URI += " \
    crate://crates.io/autocfg/1.5.1 \
    crate://crates.io/az/1.2.1 \
    crate://crates.io/bitflags/2.13.1 \
    crate://crates.io/byte-slice-cast/1.2.3 \
    crate://crates.io/byteorder/1.5.0 \
    crate://crates.io/display-interface/0.5.0 \
    crate://crates.io/display-interface-i2c/0.5.0 \
    crate://crates.io/display-interface-spi/0.5.0 \
    crate://crates.io/embedded-graphics/0.8.2 \
    crate://crates.io/embedded-graphics-core/0.4.1 \
    crate://crates.io/embedded-hal/1.0.0 \
    crate://crates.io/embedded-hal-async/1.0.0 \
    crate://crates.io/float-cmp/0.9.0 \
    crate://crates.io/maybe-async-cfg/0.2.4 \
    crate://crates.io/memchr/2.8.3 \
    crate://crates.io/micromath/2.1.0 \
    crate://crates.io/num-traits/0.2.19 \
    crate://crates.io/pin-project-lite/0.2.17 \
    crate://crates.io/proc-macro-error/1.0.4 \
    crate://crates.io/proc-macro-error-attr/1.0.4 \
    crate://crates.io/proc-macro2/1.0.107 \
    crate://crates.io/pulldown-cmark/0.11.3 \
    crate://crates.io/quote/1.0.47 \
    crate://crates.io/spin/0.12.3 \
    crate://crates.io/ssd1306/0.10.0 \
    crate://crates.io/syn/1.0.109 \
    crate://crates.io/tokio/1.53.1 \
    crate://crates.io/unicase/2.9.0 \
    crate://crates.io/unicode-ident/1.0.24 \
    crate://crates.io/version_check/0.9.5 \
"

FIRMWARE_SOURCE_DIR ??= "${TOPDIR}/../.."
EXTERNALSRC = "${FIRMWARE_SOURCE_DIR}"
EXTERNALSRC_BUILD = "${WORKDIR}/build"
SOURCE_BASEDIR = "${EXTERNALSRC}/apps/firmware"
CARGO_MANIFEST_PATH = "${SOURCE_BASEDIR}/yocto/Cargo.toml"

# base_do_unpack resets SOURCE_BASEDIR to EXTERNALSRC when a recipe combines an
# external tree with fetched crates. Restore the narrow source directory before
# reproducible.py scans it; scanning the whole checkout races rm_work through
# the CI-mounted .cache/yocto tree.
python firmware_limit_source_date_epoch_scan() {
    d.setVar("SOURCE_BASEDIR", d.getVar("EXTERNALSRC") + "/apps/firmware")
}
do_unpack[postfuncs] =+ "firmware_limit_source_date_epoch_scan"

FIRMWARE_FILES_DIR := "${THISDIR}/files"

SYSTEMD_SERVICE:${PN} = "firmware.service"
SYSTEMD_AUTO_ENABLE:${PN} = "enable"

do_install[file-checksums] += "${FIRMWARE_FILES_DIR}/firmware.service:True"

do_install:append() {
    install -d "${D}${systemd_system_unitdir}"
    install -m 0644 "${FIRMWARE_FILES_DIR}/firmware.service" \
        "${D}${systemd_system_unitdir}/firmware.service"
}

SRC_URI[autocfg-1.5.1.sha256sum] = "f2032f911046de80f0a198e0901378627c33f59ea0ac00e363d481118bd70a53"
SRC_URI[az-1.2.1.sha256sum] = "7b7e4c2464d97fe331d41de9d5db0def0a96f4d823b8b32a2efd503578988973"
SRC_URI[bitflags-2.13.1.sha256sum] = "b588b76d00fde79687d7646a9b5bdf3cc0f655e0bbd080335a95d7e96f3587da"
SRC_URI[byte-slice-cast-1.2.3.sha256sum] = "7575182f7272186991736b70173b0ea045398f984bf5ebbb3804736ce1330c9d"
SRC_URI[byteorder-1.5.0.sha256sum] = "1fd0f2584146f6f2ef48085050886acf353beff7305ebd1ae69500e27c67f64b"
SRC_URI[display-interface-0.5.0.sha256sum] = "7ba2aab1ef3793e6f7804162debb5ac5edb93b3d650fbcc5aeb72fcd0e6c03a0"
SRC_URI[display-interface-i2c-0.5.0.sha256sum] = "0d964fa85bbbb5a6ecd06e58699407ac5dc3e3ad72dac0ab7e6b0d00a1cd262d"
SRC_URI[display-interface-spi-0.5.0.sha256sum] = "f86b9ec30048b1955da2038fcc3c017f419ab21bb0001879d16c0a3749dc6b7a"
SRC_URI[embedded-graphics-0.8.2.sha256sum] = "4e8da660bb0c829b34a56a965490597f82a55e767b91f9543be80ce8ccb416fe"
SRC_URI[embedded-graphics-core-0.4.1.sha256sum] = "95743bef3ff70fcba3930246c4e6872882bbea0dcc6da2ca860112e0cd4bd09f"
SRC_URI[embedded-hal-1.0.0.sha256sum] = "361a90feb7004eca4019fb28352a9465666b24f840f5c3cddf0ff13920590b89"
SRC_URI[embedded-hal-async-1.0.0.sha256sum] = "0c4c685bbef7fe13c3c6dd4da26841ed3980ef33e841cddfa15ce8a8fb3f1884"
SRC_URI[float-cmp-0.9.0.sha256sum] = "98de4bbd547a563b716d8dfa9aad1cb19bfab00f4fa09a6a4ed21dbcf44ce9c4"
SRC_URI[maybe-async-cfg-0.2.4.sha256sum] = "a1e083394889336bc66a4eaf1011ffbfa74893e910f902a9f271fa624c61e1b2"
SRC_URI[memchr-2.8.3.sha256sum] = "cf8baf1c55e62ffcace7a9f06f4bd9cd3f0c4beb022d3b367256b91b87513d98"
SRC_URI[micromath-2.1.0.sha256sum] = "c3c8dda44ff03a2f238717214da50f65d5a53b45cd213a7370424ffdb6fae815"
SRC_URI[num-traits-0.2.19.sha256sum] = "071dfc062690e90b734c0b2273ce72ad0ffa95f0c74596bc250dcfd960262841"
SRC_URI[pin-project-lite-0.2.17.sha256sum] = "a89322df9ebe1c1578d689c92318e070967d1042b512afbe49518723f4e6d5cd"
SRC_URI[proc-macro-error-1.0.4.sha256sum] = "da25490ff9892aab3fcf7c36f08cfb902dd3e71ca0f9f9517bea02a73a5ce38c"
SRC_URI[proc-macro-error-attr-1.0.4.sha256sum] = "a1be40180e52ecc98ad80b184934baf3d0d29f979574e439af5a55274b35f869"
SRC_URI[proc-macro2-1.0.107.sha256sum] = "985e7ec9bb745e6ce6535b544d84d6cd6f7ad8bd711c398938ae983b91a766d9"
SRC_URI[pulldown-cmark-0.11.3.sha256sum] = "679341d22c78c6c649893cbd6c3278dcbe9fc4faa62fea3a9296ae2b50c14625"
SRC_URI[quote-1.0.47.sha256sum] = "1fbf4db142a473a8d80c26bbf18454ed458bf8d26c8219c331daecfdbd079001"
SRC_URI[spin-0.12.3.sha256sum] = "0134f9043ed38b087ac4f7d4af44c79e2c9e5094421fe3164f435ce585953b10"
SRC_URI[ssd1306-0.10.0.sha256sum] = "3ea6aac2d078bbc71d9b8ac3f657335311f3b6625e9a1a96ccc29f5abfa77c56"
SRC_URI[syn-1.0.109.sha256sum] = "72b64191b275b66ffe2469e8af2c1cfe3bafa67b529ead792a6d0160888b4237"
SRC_URI[tokio-1.53.1.sha256sum] = "202caea871b69668250d242070849eb495be178ed697a3e98aebce5bc81a0bed"
SRC_URI[unicase-2.9.0.sha256sum] = "dbc4bc3a9f746d862c45cb89d705aa10f187bb96c76001afab07a0d35ce60142"
SRC_URI[unicode-ident-1.0.24.sha256sum] = "e6e4313cd5fcd3dad5cafa179702e2b244f760991f45397d14d4ebf38247da75"
SRC_URI[version_check-0.9.5.sha256sum] = "0b928f33d975fc6ad9f86c8f283853ad26bdd5b10b7f1542aa2fa15e2289105a"
