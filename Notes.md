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
* Key bank is selectable. From the MT7697 TRM:
  * N9 has EFUSEs.
  * The crypto engine can have a key programmed into it from software
    (stored in AES/DES key registers), or it can use a key directly from
    one of two banks in the EFUSEs.
  * Maybe the PDA behaves similarly, selecting a decryption key from
    multiple key banks in the EFUSEs.
    * Maybe the keys are different for each chip?
    * ~~Need to determine if PDA of MT7697 can decrypt SoC WiFi
      firmware.~~ This doesn't work--see below.
    * Need to try to read the N9 EFUSEs.


I did some experimenting with the [MT7697][mt7697] on the
[LinkIt 7697][linkit]:

* I couldn't get the PDA in the MT7697 to decrypt code for either the
  MT6735 or MT6797.
  * Maybe the keys that are selectable in the four keyslots are
    SoC-family-specific or even SoC-class specific (e.g., "IoT" vs.
    "smartphone/tablet").
  * Maybe I messed up and tried decrypting the wrong data, resulting in
    the garbled decryption output.
    * I'll have to try this again with different input data, just to be
      sure.
* Trying to configure the PDA to operate on any data that isn't a
  multiple of 16 bytes fails when done through the SDIO interface.
  * Reconfiguring the PDA through its register interface enables sending
    data in multiples of four bytes, but it still does its decryption
    operation on blocks of 16 bytes.


Important values:

* IoT firmware `E_K(zeros)`: `1af02af42f0fb9677bba9808d797ffce`
* SoC firmware `E_K(zeros)`: `b48d136fe376127cc5f91fb483e9d660`
* SoC firmware IV: `00000000000000000000000000000000`


[trm]: https://web.archive.org/web/20201101093239if_/https://labs.mediatek.com/en/download/6OPabr6H
[docs]: https://web.archive.org/web/20210510020710/https://docs.labs.mediatek.com/resource/mt7687-mt7697/en/documentation
[mt7697]: https://web.archive.org/web/20210927020259/https://labs.mediatek.com/en/chipset/MT7697
[linkit]: https://web.archive.org/web/20210927020259/https://labs.mediatek.com/en/chipset/MT7697#HDK
