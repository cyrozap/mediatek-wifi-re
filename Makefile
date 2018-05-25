all: mediatek_soc_wifi_firmware.py

%.py: %.ksy
	kaitai-struct-compiler -t python $<
