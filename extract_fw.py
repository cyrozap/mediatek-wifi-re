#!/usr/bin/env python3

import binascii
import struct
import sys
from zlib import crc32

import mediatek_soc_wifi_firmware

e_keys = [
    bytearray(16),
]

w_key = bytearray(16)

if __name__ == "__main__":
    orig = sys.argv[1]
    ext = "bin"
    basename = orig

    fw_bytes = open(orig, 'rb').read()
    fw = mediatek_soc_wifi_firmware.MediatekSocWifiFirmware.from_bytes(fw_bytes)
    if fw.signature not in ("MTKE", "MTKW"):
        print("Error: Unrecognized firmware signature \"{}\"".format(fw.signature), file=sys.stderr)
        sys.exit(1)
    header = fw.header
    calculated_crc = crc32(fw_bytes[8:])
    if calculated_crc != header.crc:
        print("CRC BAD: Expected 0x{:08x}, got 0x{:08x}.".format(header.crc, calculated_crc))
    else:
        print("CRC OK")
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
