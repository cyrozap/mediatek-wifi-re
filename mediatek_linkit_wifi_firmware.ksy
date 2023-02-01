meta:
  id: mediatek_linkit_wifi_firmware
  endian: le
  title: MediaTek LinkIt WiFi Firmware
  license: CC0-1.0
seq:
  - id: image_size
    type: u4
  - id: image
    type: image
    size: image_size - 4
  - id: patch_size
    type: u4
  - id: patch
    type: patch
    size: patch_size - 4
types:
  image:
    seq:
      - id: ilm_pda_packets
        type: pda_packets
        size: fw_image_tailer.ilm_info.len + 4 + 12 * 4
        doc: "ILM length + 4-byte CRC + one 12-byte header per packet."
      - id: dlm_pda_packets
        type: pda_packets
        size: fw_image_tailer.dlm_info.len + 4 + 12 * 1
        doc: "DLM length + 4-byte CRC + one 12-byte header per packet."
    instances:
      fw_image_tailer:
        pos: _io.size - 36 * 2
        type: fw_image_tailer
  pda_packets:
    seq:
      - id: pda_packets
        type: pda_packet
        repeat: eos
  pda_packet:
    seq:
      - id: pda_packet_header
        type: pda_packet_header
      - id: pda_packet_data
        size: pda_packet_header.len - 12
  pda_packet_header:
    seq:
      - id: len
        type: u4
      - id: unk
        size: 8
  patch:
    seq:
      - id: header
        type: patch_header
      - id: data
        size-eos: true
        type: patch_body
  patch_header:
    seq:
      - id: built_date
        size: 16
        type: str
        encoding: ASCII
      - id: platform
        size: 4
      - id: hw_ver
        type: u2be
      - id: sw_ver
        type: u2be
      - id: reserved
        size: 4
      - id: crc
        type: u2
  patch_body:
    seq:
      - id: enabled_patches
        size: 8
        doc: "Little-endian 64-bit bitfield of enabled patches."
      - id: patch_dst_list
        type: u4
        repeat: expr
        repeat-expr: 64
      - id: patch_src_list
        type: u4
        repeat: expr
        repeat-expr: 64
      - id: patch_data
        size-eos: true
  fw_image_tailer:
    seq:
      - id: ilm_info
        type: info
        size: 36
      - id: dlm_info
        type: info
        size: 36
    types:
      info:
        seq:
          - id: addr
            type: u4
          - id: chip_info
            type: u1
          - id: feature_set
            type: feature_set
          - id: ram_version
            size: 10
          - id: ram_built_date
            size: 16
          - id: len
            type: u4
        types:
          feature_set:
            seq:
              - id: reserved
                type: b5
              - id: key_index
                type: b2
              - id: encrypt_mode
                type: b1
