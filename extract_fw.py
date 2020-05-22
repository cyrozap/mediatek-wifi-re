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
    chunk_count = len(obfs_chunks)
    for chunk_i in range(1, chunk_count):
        second_prev_chunk_i = chunk_i - 2
        prev_chunk_i = chunk_i - 1
        curr_chunk_i = chunk_i
        next_chunk_i = chunk_i + 1

        # Check if the current obfuscated chunk is equivalent to an encrypted
        # block of 16 null bytes. i.e., C_i == E_K(zeroes)
        if obfs_chunks[curr_chunk_i] == ek_zero:
            # It was, so that means that the plaintext of the current chunk is
            # all zeros.
            deobfs_chunks[curr_chunk_i] = bytes(bytearray(block_size))

            # Beause a ciphertext block is equal to the XOR of its encripted
            # plaintext and the plaintext of the block that precedes it, and we
            # know that the ciphertext of the current block ("C_i") is equal to
            # a known encrypted block ("E_K(zeroes)"), that means the plaintext
            # of the previous chunk is all zeros. i.e.,
            # "C_i = E_K(P_i) XOR P_i_minus_1", and since for the current block
            # "C_i == E_K(P_i)", that means "C_i = C_i XOR P_i_minus_1", and
            # after XOR-ing each side by C_i, "zeroes = P_i_minus_1", or
            # "P_i_minus_1 = zeroes".
            deobfs_chunks[prev_chunk_i] = bytes(bytearray(block_size))

            # As we've just established, the plaintext of the previous block is
            # all zeroes ("P_i_minus_1 == zeroes"), and because we know the
            # encrypted value of a plaintext block of zeroes
            # ("E_K(P_i_minus_1) == E_K(zeroes)", and "E_K(zeroes)" is known),
            # we can now solve the equation
            # "C_i_minus_1 = E_K(P_i_minus_1) XOR P_i_minus_2" for the plaintext
            # of the second previous block, "P_i_minus_2". To do this, we simply
            # need to substitute in "E_K(zeroes)" for "E_K(P_i_minus_1)" and
            # then XOR both sides by "E_K(zeroes)". So now we have
            # "C_i_minus_1 XOR E_K(zeroes) = P_i_minus_2", or
            # "P_i_minus_2 = C_i_minus_1 XOR E_K(zeroes)". In other words, the
            # plaintext of the second previous block is equal to the XOR of the
            # ciphertext of the previous block and the encrypted block of 16
            # null bytes.
            plaintext_i2 = xor(obfs_chunks[prev_chunk_i], ek_zero)
            if curr_chunk_i == 1:
                # If the current chunk is 1, the previous chunk is 0, and the
                # second previous chunk is -1. Chunk -1 doesn't exist in the
                # obfuscated firmware--rather, the plaintext we calculated for
                # chunk -1 is the IV that gets XORed with the 0th block of
                # encrypted data to create the 0th block of obfuscated data, and
                # it's the same for every firmware for that SoC.
                print("Found IV: {}".format(plaintext_i2.hex()))
            else:
                deobfs_chunks[second_prev_chunk_i] = plaintext_i2

            # Since we know the plaintext of the 2nd previous chunk, if we know
            # its ciphertext ("C_i") is equal to its encrypted plaintext
            # ("E_K(P_i)"), add the C_i/E_K(P_i):P_i mapping to a lookup table
            # so we can decrypt that E_K(P_i) if we ever see it again.
            if second_prev_chunk_i in ci_equals_ek_pi:
                ek_pi_to_pi[obfs_chunks[second_prev_chunk_i]] = plaintext_i2

            # Make sure we're not on the last chunk to avoid indexing errors.
            if next_chunk_i < chunk_count:
                # The plaintext of the current chunk is all zeroes
                # ("P_i == zeroes"), and since
                # "C_i_plus_1 = E_K(P_i_plus_1) XOR P_i", the next ciphertext
                # ("C_i_plus_1") is equal to its encrypted plaintext
                # ("E_K(P_i_plus_1)"), or "C_i_plus_1 == E_K(P_i_plus_1)". This
                # is useful to know, so we store the index of this chunk in a
                # set to use in later loop iterations. We skip blocks of
                # encrypted zeroes because we already handle them separately.
                if deobfs_chunks[next_chunk_i] != ek_zero:
                    ci_equals_ek_pi.add(next_chunk_i)

    chunks_deobfuscated_successfully = 0
    for chunk_i in range(chunk_count):
        if deobfs_chunks[chunk_i] != obfs_chunks[chunk_i]:
            chunks_deobfuscated_successfully += 1

    print("Deobfuscated {} of {} blocks ({:.2f}%).".format(chunks_deobfuscated_successfully, chunk_count,
        (100*chunks_deobfuscated_successfully)/chunk_count))

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
        open(filename, 'wb').write(data)
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
            filename = "{}.file_idx_{}.dest_addr_{:02X}.deobfs.{}".format(basename, i, section.dest_addr, ext)
            open(filename, 'wb').write(data)
