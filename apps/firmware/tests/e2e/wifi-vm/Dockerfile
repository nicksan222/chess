FROM ubuntu:24.04

RUN apt-get update -qq \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y -qq --no-install-recommends \
        qemu-system-x86 qemu-utils genisoimage \
    && rm -rf /var/lib/apt/lists/*

# Pinned Ubuntu cloud image: the guest kernel is 6.8.0-139-generic.
ADD --checksum=sha256:612b2c0cc1bc413a6cb8c38fd611794caf0f2b436c50013d8b3794db12ad7354 \
    https://cloud-images.ubuntu.com/noble/20260911/noble-server-cloudimg-amd64.img /ubuntu.img

COPY user-data meta-data bootstrap.sh start.sh /
ENTRYPOINT ["/bin/bash", "/start.sh"]
