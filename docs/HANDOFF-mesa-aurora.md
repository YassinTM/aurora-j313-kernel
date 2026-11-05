# Handoff: CI Aurora kernel hangs niri → install mesa-aurora

**Status 2026-11-05:** steps 1–4 done (`~/install-mesa-aurora.sh`). mesa-aurora 26.3.0-18 installed; it also
ships `asahi_dri.so`, so the hand-built `asahi`-named kernel keeps GPU acceleration (verified: renderer
`Apple M1 (G13G B1)`). Asahi COPR mesa repo got `excludepkgs=mesa*`. Instead of step 5, the CI kernel was set
with `grub2-reboot` (one boot only); the default stays `7.3.0-aurora-j313+` until the CI kernel is verified.

Written 2026-11-05 for the next agent working on asahi-mac (M1 Air J313, Fedora Asahi Remix 44, niri + Noctalia).
Read `~/.claude/CLAUDE.md` first: use `pkexec`, never `sudo`, and batch root work into as few prompts as possible.

## What happened

- The user installed the first GitHub Actions build, `kernel-aurora-j313-7.3.0-18.1.fc44.aurora.j313.aarch64`
  (Aurora commit `2661d71e1`, pinned in `upstream.json`). After a TTY login with the fingerprint reader, niri
  never draws anything. The last line on screen is a harmless `systemctl --user import-environment`
  deprecation warning from `/usr/bin/niri-session` line 36. Ignore that line; it has nothing to do with the hang.
- **Root cause:** the latest Aurora tree renamed the GPU DRM driver from `asahi` to **`aurora`**
  (`drivers/gpu/drm/asahi/driver.rs`: `name: c"aurora"`, module `aurora.ko`). Aurora pairs this with its own
  Mesa (`mesa-aurora`). Fedora's `mesa-dri-drivers-26.2.4` doesn't recognize the `aurora` driver. Even with
  `MESA_LOADER_DRIVER_OVERRIDE=asahi` it falls back to llvmpipe. The niri journal shows
  `MESA: error: ZINK: failed to choose pdev` and then `error adding device: no allocator available for device`,
  and niri keeps running with no output.
- The hand-built **`7.3.0-aurora-j313+`** still works. It was built on 2026-11-02 from `~/linux-aurora`
  before the rename, so its module is still `asahi.ko`. The source tree at `~/linux-aurora` has moved on since
  and now includes the rename too, so rebuilding from it won't help.

## User's decision

Keep GitHub CI building the **latest** Aurora kernel, with no local compiling. Get a matching Mesa
**prebuilt** from Aurora's signed dnf repo, and limit that repo to Mesa only.

## Steps (run from a working desktop on `7.3.0-aurora-j313+`, so the polkit GUI agent can prompt)

1. Make the working kernel the default in case the next boot isn't watched:
   `grubby --set-default /boot/vmlinuz-7.3.0-aurora-j313+`
2. Add Aurora's repo, **restricted to Mesa** (`/etc/yum.repos.d/aurora-mesa.repo`):
   ```ini
   [aurora-mesa]
   name=Aurora Silicon for Fedora (Mesa only)
   baseurl=https://aurorasilicon.org/fedora-aurora/$releasever/testing/aarch64
   enabled=1
   gpgcheck=1
   repo_gpgcheck=0
   gpgkey=https://raw.githubusercontent.com/aurora-silicon/fedora-aurora/main/packages/aurora-repos/RPM-GPG-KEY-aurora
   includepkgs=mesa-aurora*
   priority=1
   ```
   Key fingerprint to verify (from `keys/fingerprint.txt` in aurora-silicon/fedora-aurora):
   `D6C974933C41AACE00AE3C4591B639B8C6A77AC1`. Download the key, check it with `gpg --show-keys`, then
   `rpm --import` it.
   Upstream's own `aurora.repo` is the same baseurl without `includepkgs`. **Don't** install `aurora-repos`:
   it would bring in Aurora's whole package set (fprintd, upower, mutter, …).
   Also check for conflicts with the existing `copr:group_asahi:mesa` repo. It may need
   `excludepkgs=mesa*` or to be disabled so dnf doesn't swap back and forth.
3. Swap in the Mesa packages. Their specs `Provides` and `Obsoletes` Fedora's `mesa-dri-drivers`, `mesa-libEGL`,
   `mesa-libGL`, `mesa-libgbm`, `mesa-vulkan-drivers`, and so on:
   `dnf install --allowerasing mesa-aurora-dri-drivers mesa-aurora-vulkan-drivers`
   Check the dnf transaction before confirming. It should replace only mesa-* packages. If you're unsure, ask the user.
   Steps 1–3 can go in one `pkexec bash -c '…'` (one password prompt).
4. Add a guard to `tools/aurora-kernel-update` (this repo, symlinked into `~/.local/bin`): refuse to install a
   kernel whose GPU driver is `aurora` unless `rpm -q mesa-aurora-dri-drivers` succeeds. A plain
   `rpm -q mesa-aurora-dri-drivers || { echo "install mesa-aurora first"; exit 1; }` before the `dnf install`
   at line ~68 is enough. Commit it here. Push from dev-agent, which has gh auth; asahi has no push rights.
5. Set the default back to the CI kernel (`grubby --set-default /boot/vmlinuz-7.3.0-18.1.fc44.aurora.j313.aarch64`)
   and have the user reboot into it.

## Verify (on the CI kernel)

- `journalctl -b --user -u niri.service | grep -E "ZINK|no allocator"` should print nothing.
- The renderer should be AGX, not llvmpipe, e.g. `eglinfo -B` (package `mesa-demos`) or
  `python3 -I docs/egltest.py` (prints the GL renderer of /dev/dri/renderD128).
- External monitor, fingerprint login, and audio still work.

## Side effects / rollback

- After the swap, the hand-built `asahi`-named kernel and the stock `kernel-16k` will probably lose GPU
  acceleration, so they're no longer clean graphical fallbacks. A TTY still works on them.
- Rollback: `dnf swap mesa-aurora-dri-drivers mesa-dri-drivers` (plus the vulkan package), disable the
  `aurora-mesa` repo, and boot `7.3.0-aurora-j313+`.
- Update the memory file `asahi-mac-laptop.md` when done.
