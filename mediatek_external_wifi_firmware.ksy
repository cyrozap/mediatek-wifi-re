meta:
  id: mediatek_external_wifi_firmware
  endian: le
  title: MediaTek External WiFi Firmware
  license: CC0-1.0
seq:
  - id: ilm
    size: fw_image_tailer.ilm_info.len + 4
  - id: dlm
    size: fw_image_tailer.dlm_info.len + 4
instances:
  fw_image_tailer:
    pos: _io.size - 36 * 2
    type: fw_image_tailer
types:
  fw_image_tailer:
    seq:
      - id: ilm_info
        type: info
      - id: dlm_info
        type: info
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
