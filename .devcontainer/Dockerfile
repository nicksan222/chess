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
        libudev-dev \
        libusb-1.0-0-dev \
        make \
        pkg-config \
        usbutils \
        xz-utils \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

RUN rustup component add clippy rustfmt \
    && rustup target add thumbv8m.main-none-eabihf
