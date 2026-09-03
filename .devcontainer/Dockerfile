# Build context is the repository root (see devcontainer.json).
ARG VARIANT="ubuntu-24.04"
FROM mcr.microsoft.com/devcontainers/base:${VARIANT}

ARG BLENDER_VERSION="4.5.13"
ARG KICAD_PPA="ppa:kicad/kicad-9.0-releases"
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
        libdecor-0-plugin-1-cairo \
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
        software-properties-common \
        pkg-config \
        python3 \
        python3-pip \
        python3-venv \
        shellcheck \
        usbutils \
        xauth \
        xvfb \
        xdotool \
        xz-utils \
    && add-apt-repository --yes "${KICAD_PPA}" \
    && apt-get update \
    && apt-get install --yes --no-install-recommends kicad \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages --no-cache-dir ruff==0.16.5

RUN archive="blender-${BLENDER_VERSION}-linux-x64.tar.xz" \
    && curl --fail --location --retry 3 --show-error \
        --output "/tmp/${archive}" \
        "https://download.blender.org/release/Blender${BLENDER_VERSION%.*}/${archive}" \
    && printf '%s  %s\n' "${BLENDER_SHA256}" "/tmp/${archive}" \
        | sha256sum --check --status \
    && tar -xf "/tmp/${archive}" -C /opt \
    && mv "/opt/blender-${BLENDER_VERSION}-linux-x64" /opt/blender \
    && rm "/tmp/${archive}"

ENV BLENDER_BIN=/opt/blender/blender \
    PATH="/home/vscode/.cargo/bin:${PATH}"

USER vscode
RUN curl --fail --location --proto '=https' --tlsv1.2 --show-error \
        https://sh.rustup.rs \
        | sh -s -- -y --profile minimal --default-toolchain stable \
    && rustup component add clippy rustfmt rust-src \
    && cargo install just --locked --version 1.40.0
USER root
