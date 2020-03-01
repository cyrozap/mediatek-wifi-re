#!/usr/bin/env python3

import argparse
import binascii
import struct
import sys
from zlib import crc32

import mediatek_soc_wifi_firmware

e_keys = [
    bytes.fromhex("B4 8D 13 6F E3 76 12 7C  C5 F9 1F B4 83 E9 D6 60".replace(' ','')),
]

w_key = bytes.fromhex("B4 8D 13 6F E3 76 12 7C  C5 F9 1F B4 83 E9 D6 60".replace(' ',''))

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("input", type=str, help="Input file.")
    parser.add_argument("-d", "--deobfs", dest="deobfsuscate", action="store_true", help="Deobfuscate the firmware, if necessary.")
    parser.add_argument("-e", "--no-deobfs", dest="deobfsuscate", action="store_false", help="Don't deobfuscate the firmware, even if it's marked as obfuscated. (default behavior)")
    parser.set_defaults(deobfsuscate=False)
    #parser.add_argument("-o", "--output", type=str, help="Output file.")
    args = parser.parse_args()

    orig = args.input
    ext = "bin"
    basename = orig

    fw_bytes = open(orig, 'rb').read()
    fw = mediatek_soc_wifi_firmware.MediatekSocWifiFirmware.from_bytes(fw_bytes)
    if fw.signature not in ("MTKE", "MTKW"):
        print("Error: Unrecognized firmware signature \"{}\"".format(fw.signature), file=sys.stderr)
        sys.exit(1)
    firmware = fw.firmware
    calculated_crc = crc32(fw_bytes[8:])
    if calculated_crc != firmware.crc:
        print("CRC BAD: Expected 0x{:08x}, got 0x{:08x}.".format(firmware.crc, calculated_crc))
    else:
        print("CRC OK")
    for i in range(len(firmware.fwdl_sections)):
        section = firmware.fwdl_sections[i]

        filename = "{}.file_idx_{}.dest_addr_{:02X}.{}".format(basename, i, section.dest_addr, ext)
        data = section.data
        if args.deobfsuscate:
            if fw.signature == "MTKE":
                if section.enc == 1:
                    key = e_keys[section.k_idx]
                    data = fw._io.process_xor_many(section.data, key)
            elif fw.signature == "MTKW":
                data = fw._io.process_xor_many(section.data, w_key)
        open(filename, 'wb').write(data)
