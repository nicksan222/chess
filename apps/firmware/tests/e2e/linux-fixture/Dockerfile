FROM ubuntu:24.04

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        dbus network-manager \
    && rm -rf /var/lib/apt/lists/*

COPY start.sh /start.sh
ENTRYPOINT ["/bin/sh", "/start.sh"]
