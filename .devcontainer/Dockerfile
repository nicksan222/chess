# Build context is the repository root (see devcontainer.json).
ARG VARIANT="1-bookworm"
FROM mcr.microsoft.com/devcontainers/rust:${VARIANT}

ARG BLENDER_VERSION="4.5.13"
ARG BLENDER_SHA256="da4e69b06b75b9e642d106496c50e7e240218b411d2f6e18271c1d1d819cef91"

RUN apt-get update \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install --yes --no-install-recommends \
        bash-completion \
        ca-certificates \
        clang \
        cmake \
        curl \
        git \
        libdecor-0-0 \
        libdecor-0-plugin-1 \
        libegl1 \
        libgl1 \
        libgl1-mesa-dri \
        libgles2 \
        libice6 \
        libsm6 \
        libudev-dev \
        libusb-1.0-0-dev \
        libx11-6 \
        libxext6 \
        libxfixes3 \
        libxi6 \
        libxkbcommon0 \
        libxrender1 \
        make \
        pkg-config \
        python3 \
        python3-pip \
        python3-venv \
        shellcheck \
        usbutils \
        xauth \
        xvfb \
        xz-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN archive="blender-${BLENDER_VERSION}-linux-x64.tar.xz" \
    && curl --fail --location --retry 3 --show-error \
        --output "/tmp/${archive}" \
        "https://download.blender.org/release/Blender${BLENDER_VERSION%.*}/${archive}" \
    && printf '%s  %s\n' "${BLENDER_SHA256}" "/tmp/${archive}" \
        | sha256sum --check --status \
    && tar -xf "/tmp/${archive}" -C /opt \
    && mv "/opt/blender-${BLENDER_VERSION}-linux-x64" /opt/blender \
    && rm "/tmp/${archive}"

COPY hardware/pcb/requirements.txt /tmp/pcb-requirements.txt
RUN python3 -m venv /opt/pcb \
    && /opt/pcb/bin/pip install --upgrade pip \
    && /opt/pcb/bin/pip install -r /tmp/pcb-requirements.txt \
    && rm /tmp/pcb-requirements.txt

ENV BLENDER_BIN=/opt/blender/blender \
    PATH="/opt/pcb/bin:${PATH}"

USER vscode
RUN rustup component add clippy rustfmt rust-src
USER root
