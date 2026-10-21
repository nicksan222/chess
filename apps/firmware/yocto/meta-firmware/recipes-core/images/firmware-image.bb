SUMMARY = "Flashable Raspberry Pi firmware"
LICENSE = "MIT"

require recipes-core/images/core-image-minimal.bb

# The firmware service and the Wi-Fi stack it provisions through NetworkManager.
IMAGE_INSTALL:append = " \
    firmware \
    networkmanager-daemon \
    networkmanager-wifi \
    wpa-supplicant \
    dnsmasq \
"

# A compressed SD card image plus a block map for fast flashing with bmaptool.
IMAGE_FSTYPES:append = " wic.xz wic.bmap"
