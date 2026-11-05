This repository builds a kernel RPM for one MacBook Air M1 (Apple J313, t8103)
that follows Aurora's Fedora kernel package (aurora-silicon/fedora-aurora,
packages/kernel-aurora). Aurora just changed that package. You get the diff of
their packaging (spec without changelog, fedora.config, validate-config.py),
plus our spec template and our config fragment.

Our spec deliberately leaves out the `aura` requirement (Stage 2 bootloader,
needed for SN012776 amps, which J313 does not have) and the aurora-userpages
subpackage, and installs device trees under /boot/dtb-<krel>.

In GitHub markdown, briefly: what did Aurora change, does our spec template or
config fragment need a matching change for this Mac (quote the lines to add or
change), or can it be ignored? Say clearly when you are unsure.
