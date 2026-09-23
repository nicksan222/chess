#!/bin/sh
set -eu

dbus-daemon --system --fork
NetworkManager --no-daemon &

# Wait for the real daemon, not merely for the D-Bus socket to exist.
ready=0
for _ in $(seq 1 30); do
    if nmcli --wait 1 -t -f STATE general status >/dev/null 2>&1; then
        ready=1
        break
    fi
    sleep 1
done
if [ "$ready" -ne 1 ]; then
    echo 'NetworkManager did not become ready' >&2
    exit 1
fi

echo 'NetworkManager ready'
exec sleep infinity
