# Notes

* Kernel code is in `drivers/misc/mediatek/connectivity/wlan`.
  * From there, interesting definitions are in
    `./gen2/include/wlan_lib.h` and `./gen3/include/wlan_lib.h`.
  * Firmware loading code is in `./gen2/common/wlan_lib.c` and
    `./gen3/common/wlan_lib.c`.
  * The kernel code for later SoCs generally accounts for more hardware
    variations than the code for earlier SoCs.
* Code and data are loaded by segment into different memory regions.
* The CPU architecture of the code portions is NDS32, which is
  consistent with other MediaTek WiFi chips.
* Some code is obfuscated using what appears to be a simple cyclic XOR,
  but guessing the key hasn't garnered any useful results.
* Deobfuscation doesn't seem to happen in the Linux kernel driver.
* I doubt that the deobfuscation is happening in dedicated hardware. The
  state machine to check the header, verify the checksum, and load and
  deobfuscate each segment would be far too complicated.
* Since this code is called `WIFI_RAM_CODE*`, maybe the NDS32 core has
  a boot ROM that does the deobfuscation?
* Maybe the NDS32 boot ROM can be dumped from the AP?
* The [MT76x7 Technical Reference Manual][trm] (found [here][docs])
  lists a "Patch Decryption Accelerator" (PDA) in the N9 CPU memory map,
  so I'm probably partially correct in that the boot ROM performs the
  firmware image parsing but the decryption is performed by dedicated
  hardware.
  * That said, just because the hardware is called a "decryption"
    accelerator doesn't necessarily mean the decryption is actually
    cryptographically secure, especially since there is already a
    dedicated cryptography accelerator on the same bus and in this
    context it wouldn't make sense to include two pieces of hardware
    that have the same function.


[trm]: https://web.archive.org/web/20201101093239if_/https://labs.mediatek.com/en/download/6OPabr6H
[docs]: https://web.archive.org/web/20210510020710/https://docs.labs.mediatek.com/resource/mt7687-mt7697/en/documentation
