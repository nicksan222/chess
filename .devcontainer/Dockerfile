# Build context is the repository root (see devcontainer.json).
ARG VARIANT="ubuntu-24.04"
FROM mcr.microsoft.com/devcontainers/base:${VARIANT}

ARG CLAUDE_VERSION="2.1.287"
ARG HERDR_VERSION="0.9.3"
ARG BLENDER_VERSION="4.5.13"
ARG KICAD_PPA="ppa:kicad/kicad-9.0-releases"
ARG BLENDER_SHA256="da4e69b06b75b9e642d106496c50e7e240218b411d2f6e18271c1d1d819cef91"

RUN apt-get update \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install --yes --no-install-recommends \
        bash-completion \
        bzip2 \
        ca-certificates \
        chrpath \
        clang \
        cmake \
        cpio \
        curl \
        debianutils \
        diffstat \
        file \
        gawk \
        gcc-aarch64-linux-gnu \
        git \
        gh \
        iputils-ping \
        libc6-dev-arm64-cross \
        libdecor-0-0 \
        libdecor-0-plugin-1-cairo \
        libegl1 \
        libgl1 \
        libgl1-mesa-dri \
        libgles2 \
        libice6 \
        libsm6 \
        liblz4-tool \
        libudev-dev \
        libusb-1.0-0-dev \
        libx11-6 \
        libxext6 \
        libxfixes3 \
        libxi6 \
        libxkbcommon0 \
        libxrender1 \
        locales \
        make \
        ngspice \
        software-properties-common \
        pkg-config \
        python3 \
        python3-git \
        python3-jinja2 \
        python3-pexpect \
        python3-pip \
        python3-venv \
        shellcheck \
        socat \
        texinfo \
        unzip \
        usbutils \
        wget \
        xauth \
        xvfb \
        xdotool \
        xz-utils \
        zstd \
    && for attempt in 1 2 3; do \
        add-apt-repository --yes "${KICAD_PPA}" && break; \
        if [ "${attempt}" -eq 3 ]; then exit 1; fi; \
        echo "KiCad PPA unavailable; retrying (${attempt}/3)..."; \
        sleep 15; \
    done \
    && apt-get update \
    && apt-get install --yes --no-install-recommends kicad \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages --no-cache-dir \
        basedpyright==1.40.0 \
        blender-python-stubs==4.5.8.1 \
        kas==5.2 \
        ruff==0.16.5

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
    PATH="/home/vscode/.local/bin:/home/vscode/.cargo/bin:${PATH}"

USER vscode
RUN curl --fail --location --proto '=https' --tlsv1.2 --show-error \
        https://sh.rustup.rs \
        | sh -s -- -y --profile minimal --default-toolchain stable \
    && rustup component add clippy rustfmt rust-src \
    && rustup target add aarch64-unknown-linux-gnu \
    && cargo install just --locked --version 1.40.0

# Native Claude and checksum-verified Herdr; login happens only at runtime.
ENV DISABLE_AUTOUPDATER=1
RUN curl --fail --location --retry 3 --show-error \
        --output /tmp/claude-install.sh https://claude.ai/install.sh \
    && bash /tmp/claude-install.sh "${CLAUDE_VERSION}" \
    && rm /tmp/claude-install.sh \
    && case "$(uname -m)" in \
        x86_64) arch=x86_64; checksum=18a8dc65f1c2fa485884344356dea1cfd911c6f06cf46fa78e193f4087f4dba7 ;; \
        aarch64) arch=aarch64; checksum=4de7aa3e25678812e92960de64f7c2aaa1bca1f0f80a3c5e559837e231e1f5c0 ;; \
        *) echo "Unsupported Herdr architecture" >&2; exit 1 ;; \
    esac \
    && mkdir -p /home/vscode/.local/bin \
    && curl --fail --location --retry 3 --show-error \
        --output /home/vscode/.local/bin/herdr \
        "https://github.com/herdrdev/herdr/releases/download/v${HERDR_VERSION}/herdr-linux-${arch}" \
    && printf '%s  /home/vscode/.local/bin/herdr\n' "${checksum}" | sha256sum --check \
    && chmod +x /home/vscode/.local/bin/herdr
USER root
