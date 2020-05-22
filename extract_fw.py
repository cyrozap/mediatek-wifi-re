#!/usr/bin/env python3

import argparse
import binascii
import struct
import sys
from zlib import crc32

import mediatek_soc_wifi_firmware


# https://stackoverflow.com/a/9831671
ONE_BITS = bytes(bin(x).count("1") for x in range(256))


def xor(a, b):
    '''XOR two byte arrays of equal length.'''

    assert len(a) == len(b)

    size = len(a)
    q = bytearray(size)
    for i in range(size):
        q[i] = (a[i] ^ b[i]) & 0xff
    return bytes(q)

def bit_similarity(xored):
    '''Calculate the similarity of two byte arrays based on the result of their XOR.'''

    xored = bytes(xored)
    bitlen = len(xored) * 8
    ones = 0
    for byte in xored:
        ones += ONE_BITS[byte]
    return (bitlen - ones)/bitlen

def find_ek_zero_consec(obfs_chunks):
    '''Find the block most likely to be the encrypted zero block, by longest run of consecutive occurrences.'''

    block_size = len(obfs_chunks[0])

    stats = {}
    prev_chunk = None
    prev_run = None
    for curr_chunk in obfs_chunks:
        if curr_chunk == prev_chunk:
            if curr_chunk not in stats.keys():
                stats[curr_chunk] = []
            if prev_run != curr_chunk:
                stats[curr_chunk].append(0)
            stats[curr_chunk][-1] += 1
            prev_run = curr_chunk
        prev_chunk = curr_chunk

    highest = 0
    highest_chunk = None
    for (chunk, run_counts) in stats.items():
        max_count = max(run_counts)
        if max_count > highest:
            highest = max_count
            highest_chunk = chunk

    if highest_chunk is None:
        print("Error: Failed to find E_K(zeroes).")
        return None

    print("Found likeliest E_K(zeroes) \"{}\" with longest run {}.".format(highest_chunk.hex(), highest))

    similarity = bit_similarity(xor(highest_chunk, bytes(bytearray(block_size))))
    if similarity > 0.80 or similarity < 0.20:
        print("Warning: Likeliest E_K(zeroes) doesn't appear random. Are you sure this firmware is obfuscated?")

    return highest_chunk

def find_ek_zero_freq(obfs_chunks):
    '''Find the block most likely to be the encrypted zero block, by frequency.'''

    counts = {}
    for chunk in obfs_chunks:
        if chunk not in counts.keys():
            counts[chunk] = 0
        counts[chunk] += 1

    highest = 0
    highest_chunk = None
    for (chunk, count) in counts.items():
        if count > highest:
            highest = count
            highest_chunk = chunk

    print("Found likeliest E_K(zeroes) \"{}\" with frequency {}.".format(highest_chunk.hex(), highest))

    return highest_chunk

def deobfuscate(obfuscated, mode='consec'):
    obfuscated = bytes(obfuscated)
    block_size = 16
    obfs_chunks = [obfuscated[i:i+block_size] for i in range(0, len(obfuscated), block_size)]
    deobfs_chunks = obfs_chunks.copy()

    if mode == 'consec':
        ek_zero = find_ek_zero_consec(obfs_chunks)
    elif mode == 'freq':
        ek_zero = find_ek_zero_freq(obfs_chunks)
    else:
        print("Error: Unknown mode: {}".format(mode))
        return None

    if not ek_zero:
        return None

    ci_equals_ek_pi = set()
    ek_pi_to_pi = {}
    for chunk_i in range(1, len(obfs_chunks) - 1):
        if obfs_chunks[chunk_i] == ek_zero:
            # The plaintext of the 2nd previous chunk is XORed with the
            # E_K(P_i) of the previous chunk.
            plaintext_i2 = xor(obfs_chunks[chunk_i - 1], ek_zero)
            if chunk_i == 1:
                # The plaintext XORed with the 0th block of the encrypted data
                # is actually the IV.
                print("Found IV: {}".format(plaintext_i2.hex()))
            else:
                deobfs_chunks[chunk_i - 2] = plaintext_i2

            # Since we know the plaintext of the 2nd previous chunk, if we
            # know its C_i is equal to its E_K(P_i), add the C_i/E_K(P_i) to
            # a lookup table.
            if (chunk_i - 2) in ci_equals_ek_pi:
                ek_pi_to_pi[obfs_chunks[chunk_i - 2]] = plaintext_i2

            # The previous chunk is all zeros.
            deobfs_chunks[chunk_i - 1] = bytes(bytearray(block_size))

            # The current chunk is all zeros (obviously).
            deobfs_chunks[chunk_i] = bytes(bytearray(block_size))

            # The next C_i is equal to its E_K(P_i).
            if deobfs_chunks[chunk_i + 1] != ek_zero:
                ci_equals_ek_pi.add(chunk_i + 1)

    return b''.join(deobfs_chunks)


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
            deobfuscated = None
            if fw.signature == "MTKE":
                if section.enc == 1:
                    print("Section {} key index: {}".format(i, section.k_idx))
                    deobfuscated = deobfuscate(section.data)
                else:
                    print("Section {} is not encrypted.".format(i))
            elif fw.signature == "MTKW":
                deobfuscated = deobfuscate(section.data)
            if deobfuscated:
                data = deobfuscated
        open(filename, 'wb').write(data)
