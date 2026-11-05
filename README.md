# aurora-j313-kernel

The [Aurora](https://aurorasilicon.org) Linux kernel for one MacBook Air M1
(J313) on Fedora Asahi Remix 44, built as an RPM by GitHub Actions so the Mac
doesn't spend hours compiling it.

It follows Aurora's own Fedora kernel package
([fedora-aurora](https://github.com/aurora-silicon/fedora-aurora),
`packages/kernel-aurora`): same kernel commit, same config, plus:

- `patches/0001`: Force Click deep press becomes a right click.
- `patches/0002`: BCM4378 Wi-Fi bidirectional RX DMA,
  [aurora-silicon/linux#926](https://github.com/aurora-silicon/linux/pull/926)
  (not merged yet). Wi-Fi on this Mac depends on it.
- `config/j313.config`: `APPLE_SEP` etc. stay modules so `/etc/modprobe.d`
  options (Touch ID identity, `xart_guard`) keep applying.

## What runs daily

1. **Track**: when Aurora's `kernel-aurora` package moves to a new commit or
   release, copy its config into `aurora/` and pin it in `upstream.json`.
   If Aurora changed the packaging itself, open an issue.
2. **Watch PRs**: open an issue when an upstream PR in
   `patches/upstream-prs.json` is merged, closed, or changes.
3. **Check patches** against the pinned commit, with git only:
   applies → carried; reverse applies → already upstream, left out and
   reported; neither → issue, no build.
4. **Build** (`ubuntu-24.04-arm`, Fedora 44 container, about 3 hours) when
   any build input changed, then **release** the RPM with `SHA256SUMS`.

Issues get an AI read from Gemini when the `GEMINI_API_KEY` secret is set
(free tier, `gemini-3.8-flash` unless the `GEMINI_MODEL` variable says
otherwise). It only explains and proposes; nothing applies its output. For
a fix, assign the issue to Copilot and review its pull request.

## On the Mac

```sh
aurora-kernel-update --check     # anything new?
pkexec aurora-kernel-update      # install it and make it the default
```

The package installs like Fedora's kernel (`kernel-install`, dracut, GRUB
entry, device trees in `/boot/dtb-<version>`). The
`12-aurora-dtb-pin.install` hook keeps `/boot/dtb`, which m1n1 boots every
kernel with, on an Aurora device tree even when the stock kernel updates.
Two packaged versions are kept; older local builds and the stock kernel
stay in the GRUB menu until removed by hand.

When #926 is in Aurora's package, this repo can be retired in favour of
`kernel-aurora` from Aurora's repository.
