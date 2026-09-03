# Firmware

This app contains the Raspberry Pi process and its Yocto build. Docker is the
only host dependency.

```sh
just --justfile apps/firmware/justfile image-check
just --justfile apps/firmware/justfile image
```

The flashable files are written to `dist/firmware`.
