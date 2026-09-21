SUMMARY = "Flashable Raspberry Pi firmware"
LICENSE = "MIT"

require recipes-core/images/core-image-minimal.bb

IMAGE_INSTALL:append = " firmware networkmanager-daemon networkmanager-wifi wpa-supplicant dnsmasq"
IMAGE_FSTYPES:append = " wic.xz wic.bmap"
