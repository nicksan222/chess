# Firmware

This app contains the Raspberry Pi process and its Yocto build. Docker is the
only host dependency.

```sh
./tools/firmware check
./tools/firmware build
```

The flashable files are written to `dist/firmware`.
