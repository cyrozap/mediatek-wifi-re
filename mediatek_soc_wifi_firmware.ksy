meta:
  id: mediatek_soc_wifi_firmware
  endian: le
  title: MediaTek SoC WiFi Firmware
  license: CC0-1.0
seq:
  - id: firmware
    type:
      switch-on: signature
      cases:
        '"MTKE"': firmware_divided_download_e
        '"MTKW"': firmware_divided_download_w
instances:
  signature:
    pos: 0
    type: str
    size: 4
    encoding: ASCII
types:
  firmware_divided_download_e:
    seq:
      - id: signature
        contents: 'MTKE'
      - id: crc
        type: u4
        doc: CRC calculated without first 8 bytes included.
      - id: num_of_entries
        type: u4
      - id: major_number
        type: u2
      - id: minor_number
        type: u2
      - id: chip_info
        type: u4
      - id: reserved
        type: u4
      - id: fwdl_sections
        type: fwdl_section
        repeat: expr
        repeat-expr: num_of_entries
    types:
      fwdl_section:
        seq:
          - id: offset
            type: u4
          - id: k_idx
            type: u1
          - id: enc
            type: u1
          - id: reserved
            type: u2
          - id: length
            type: u4
          - id: dest_addr
            type: u4
        instances:
          data:
            io: _root._io
            pos: offset
            size: length
  firmware_divided_download_w:
    seq:
      - id: signature
        contents: 'MTKW'
      - id: crc
        type: u4
        doc: CRC calculated without first 8 bytes included.
      - id: num_of_entries
        type: u4
      - id: reserved
        type: u4
      - id: fwdl_sections
        type: fwdl_section
        repeat: expr
        repeat-expr: num_of_entries
    types:
      fwdl_section:
        seq:
          - id: offset
            type: u4
          - id: reserved
            type: u4
          - id: length
            type: u4
          - id: dest_addr
            type: u4
        instances:
          data:
            io: _root._io
            pos: offset
            size: length
