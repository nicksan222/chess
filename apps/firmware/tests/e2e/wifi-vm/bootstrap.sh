#!/bin/bash
set -euo pipefail
trap 'echo WIFI_VM_FAIL; poweroff' ERR

# Two guest-kernel radios: NetworkManager uses wlan0 and hostapd uses wlan1.
modprobe mac80211_hwsim radios=2
for _ in {1..15}; do
    [[ -e /sys/class/net/wlan1 ]] && break
    sleep 1
done
[[ -e /sys/class/net/wlan0 && -e /sys/class/net/wlan1 ]]
nmcli device set wlan1 managed no
ip addr add 10.11.12.1/24 dev wlan1
ip link set wlan1 up
dnsmasq --interface=wlan1 --bind-interfaces --port=0 \
    --dhcp-range=10.11.12.10,10.11.12.30,1h

/mnt/seed/firmware-probe
echo WIFI_VM_PASS
poweroff
