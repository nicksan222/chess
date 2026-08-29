ARG VARIANT="1-bookworm"
FROM mcr.microsoft.com/devcontainers/rust:${VARIANT}

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
        libgl1 \
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
        usbutils \
        xz-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN rustup component add clippy rustfmt \
    && rustup target add thumbv8m.main-none-eabihf
