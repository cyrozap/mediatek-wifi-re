# Notes

* Code is loaded by segment into different memory regions.
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