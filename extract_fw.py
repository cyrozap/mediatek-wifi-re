#!/usr/bin/env python3

import binascii
import struct
import sys

import mediatek_soc_wifi_firmware

e_keys = [
    bytearray(16),
]

w_key = bytearray(16)

if __name__ == "__main__":
    orig = sys.argv[1]
    ext = "bin"
    basename = orig

    fw = mediatek_soc_wifi_firmware.MediatekSocWifiFirmware.from_file(orig)
    offset = 0
    if fw.signature == "MTKE":
        header = fw.header_e
    elif fw.signature == "MTKW":
        header = fw.header_w
    else:
        print("Error: Unrecognized firmware signature \"{}\"".format(fw.signature), file=sys.stderr)
        sys.exit(1)
    for i in range(len(header.fwdl_sections)):
        info = header.fwdl_sections[i]

        filename = "{}.file_idx_{}.dest_addr_{:02X}.{}".format(basename, i, info.dest_addr, ext)
        section = fw.body[info.offset:info.offset+info.length]
        if fw.signature == "MTKE":
            if info.enc == 1:
                key = e_keys[info.k_idx]
                section = fw._io.process_xor_many(section, key)
        elif fw.signature == "MTKW":
            section = fw._io.process_xor_many(section, w_key)
        open(filename, 'wb').write(section)
