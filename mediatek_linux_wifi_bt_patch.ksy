meta:
  id: mediatek_linux_wifi_bt_patch
  endian: le
  title: MediaTek WiFi/BT Firmware Patch (Linux)
  license: CC0-1.0
seq:
  - id: header
    size: 30
    type: header
  - id: body
    size-eos: true
    type: body
types:
  header:
    # This is defined in the kernel as "mt7615_patch_hdr", but this format is
    # almost never followed correctly, so here we only parse the struct elements
    # that seem to be used consistently. The device never sees the header,
    # anyways, since the kernel always loads the firmware into the device
    # starting from byte 30 (0x1e).
    seq:
      - id: build_date
        size: 16
        type: str
        encoding: ASCII
      - id: platform
        size: 4
        type: str
        encoding: ASCII
  body:
    seq:
      - id: enabled_patches
        size: 8
        doc: "Little-endian 64-bit bitfield of enabled patches."
      - id: rom_addr_list
        type: u4
        repeat: expr
        repeat-expr: 64
        doc: "List of ROM addresses to patch with jump instructions."
      - id: jump_addr_list
        type: u4
        repeat: expr
        repeat-expr: 64
        doc: "List of jump destination addresses."
      - id: patch_data
        size-eos: true
