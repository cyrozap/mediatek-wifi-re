# MediaTek WiFi RE

Notes and utilities for reverse engineering the firmware used in MediaTek's
WiFi cores. This includes the cores used in PCIe/USB/SDIO-attached chips,
standalone WiFi microcontrollers, and SoCs with built-in WiFi.


## Quick start


### Software dependencies

* Python 3
* [Kaitai Struct Compiler][ksc]
* [Kaitai Struct Python Runtime][kspr]


### Procedure

1. Install dependencies.
2. Run `make` to generate the parser code used by `extract_fw.py`.
3. Obtain the `WIFI_RAM_CODE*` binaries you're interested in. You can
   find these on many MediaTek-based Android phones in the
   `/system/etc/firmware` directory, but if that doesn't work for you,
   you can also find these firmware files on the Internet--typically in
   the "vendor.zip" files posted by Android ROM developers. You can also
   find them, for example, using [this GitHub search query][firmware query],
   but you'll need to be logged in to GitHub in order for that to work.
4. Extract the code and data sections from each binary with
   `./extract_fw.py ...`, where `...` is the name of the
   `WIFI_RAM_CODE*` firmware binary.


## Reverse engineering notes

See [Notes.md](./Notes.md).


[ksc]: https://github.com/kaitai-io/kaitai_struct_compiler
[kspr]: https://github.com/kaitai-io/kaitai_struct_python_runtime
[firmware query]: https://github.com/search?q=filename%3AWIFI_RAM_CODE*
