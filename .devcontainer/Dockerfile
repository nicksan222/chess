# Build context is the repository root (see devcontainer.json).
ARG VARIANT="ubuntu-24.04"
FROM mcr.microsoft.com/devcontainers/base:${VARIANT}

ARG BLENDER_VERSION="4.5.13"
ARG KICAD_PPA="ppa:kicad/kicad-9.0-releases"
ARG ACTIONLINT_VERSION="1.7.12"
ARG ACTIONLINT_SHA256="8aca8db96f1b94770f1b0d72b6dddcb1ebb8123cb3712530b08cc387b349a3d8"
ARG EDITORCONFIG_CHECKER_VERSION="4.0.2"
ARG EDITORCONFIG_CHECKER_SHA256="44efaef3ed14c6ab52eb87481d78e5e5c204796dccf26e2f4598a61ba17f8003"
ARG BLENDER_SHA256="da4e69b06b75b9e642d106496c50e7e240218b411d2f6e18271c1d1d819cef91"

RUN apt-get update \
    && export DEBIAN_FRONTEND=noninteractive \
    && apt-get install --yes --no-install-recommends \
        bash-completion \
        bat \
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
        fonts-dejavu-core \
        gawk \
        gcc-aarch64-linux-gnu \
        git \
        gerbv \
        gh \
        iputils-ping \
        jq \
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
        librsvg2-bin \
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
        poppler-utils \
        python3 \
        python3-git \
        python3-jinja2 \
        python3-pexpect \
        python3-pip \
        python3-venv \
        ripgrep \
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

COPY .devcontainer/requirements.txt /tmp/requirements.txt
RUN pip3 install --break-system-packages --no-cache-dir --requirement /tmp/requirements.txt \
    && rm /tmp/requirements.txt

RUN archive="blender-${BLENDER_VERSION}-linux-x64.tar.xz" \
    && curl --fail --location --retry 3 --show-error \
        --output "/tmp/${archive}" \
        "https://download.blender.org/release/Blender${BLENDER_VERSION%.*}/${archive}" \
    && printf '%s  %s\n' "${BLENDER_SHA256}" "/tmp/${archive}" \
        | sha256sum --check --status \
    && tar -xf "/tmp/${archive}" -C /opt \
    && mv "/opt/blender-${BLENDER_VERSION}-linux-x64" /opt/blender \
    && rm "/tmp/${archive}"

RUN archive="actionlint_${ACTIONLINT_VERSION}_linux_amd64.tar.gz" \
    && curl --fail --location --retry 3 --show-error --output "/tmp/${archive}" \
        "https://github.com/rhysd/actionlint/releases/download/v${ACTIONLINT_VERSION}/${archive}" \
    && printf '%s  %s\n' "${ACTIONLINT_SHA256}" "/tmp/${archive}" | sha256sum --check --status \
    && tar -xzf "/tmp/${archive}" -C /usr/local/bin actionlint \
    && rm "/tmp/${archive}"

RUN archive="editorconfig-checker-linux-amd64.tar.gz" \
    && curl --fail --location --retry 3 --show-error --output "/tmp/${archive}" \
        "https://github.com/editorconfig-checker/editorconfig-checker/releases/download/v${EDITORCONFIG_CHECKER_VERSION}/${archive}" \
    && printf '%s  %s\n' "${EDITORCONFIG_CHECKER_SHA256}" "/tmp/${archive}" | sha256sum --check --status \
    && tar -xzf "/tmp/${archive}" -C /usr/local/bin editorconfig-checker \
    && rm "/tmp/${archive}"

ENV BLENDER_BIN=/opt/blender/blender \
    PATH="/home/vscode/.local/bin:/home/vscode/.cargo/bin:${PATH}"

COPY rust-toolchain.toml /tmp/rust-toolchain.toml
USER vscode
RUN rust_version=$(sed -n 's/^channel = "\(.*\)"$/\1/p' /tmp/rust-toolchain.toml) \
    && curl --fail --location --proto '=https' --tlsv1.2 --show-error \
        https://sh.rustup.rs \
        | sh -s -- -y --profile minimal --default-toolchain "${rust_version}" \
    && rustup component add clippy rustfmt rust-src \
    && rustup target add aarch64-unknown-linux-gnu \
    && cargo install just --locked --version 1.40.0 \
    && cargo install cargo-deny --locked --version 0.20.2 \
    && cargo install cargo-shear --locked --version 1.14.0 \
    && cargo install ast-grep --locked --version 0.51.0 \
    && cargo install typos-cli --locked --version 1.51.1

USER root
