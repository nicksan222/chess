#!/bin/bash
set -euo pipefail

genisoimage -quiet -output /seed.iso -volid cidata -joliet -rock \
    /user-data /meta-data /bootstrap.sh /firmware-probe
qemu-img create -q -f qcow2 -b /ubuntu.img -F qcow2 /guest.img

# KVM is optional: hosted CI runners without /dev/kvm still run the same guest.
if [[ -e /dev/kvm ]]; then
    accelerator=kvm
else
    accelerator=tcg
fi
exec qemu-system-x86_64 -accel "$accelerator" -m 2048 -smp 2 \
    -nographic -serial mon:stdio \
    -drive file=/guest.img,if=virtio,format=qcow2 \
    -drive file=/seed.iso,media=cdrom \
    -netdev user,id=net0 -device virtio-net-pci,netdev=net0
