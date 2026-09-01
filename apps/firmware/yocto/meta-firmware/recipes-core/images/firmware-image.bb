SUMMARY = "Flashable Raspberry Pi firmware"
LICENSE = "MIT"

require recipes-core/images/core-image-minimal.bb

IMAGE_INSTALL:append = " firmware"
IMAGE_FSTYPES:append = " wic.xz wic.bmap"
