# EchoLocal Installer — Home Assistant add-on

A Home Assistant add-on that flashes and installs [EchoLocal](https://github.com/ygelfand/echolocal)
onto an unlocked 2nd-generation Echo Dot, over USB, from the Home Assistant UI.

It wraps the upstream `echoctl` host CLI and adds nothing to it: this add-on only exists
because flashing an Echo Dot needs raw USB and `adb`, which a Home Assistant **integration**
cannot reach. An **add-on** can, and it gets an Ingress panel in the sidebar.

Scope is deliberately narrow: **install only**. It does not change Wi-Fi, rename, reinstall or
uninstall, and it adds no entities.

---

## Requirements

- **Home Assistant OS** on hardware with a free USB port (the add-on uses `usb: true`).
- An Echo Dot **already unlocked, with TWRP as its recovery**. The amonet-biscuit unlock is a
  **one-time PC step** (unplug power, hold the **action button** — the dot "•" — plug back in →
  green LED, run `fastbrick`, type `YES`). For an EchoLocal install **nothing else from the
  unlock guide is needed** — no FireOS re-flash, no root. This add-on does **not** run the
  exploit; it takes over once the device is booted into TWRP. Full flow:
  [docs/unlocking.md](docs/unlocking.md) · [XDA thread](https://xdaforums.com/t/unlock-root-twrp-unbrick-amazon-echo-dot-2nd-gen-2016-biscuit.4761416/).
- The Dot connected to the Home Assistant host by USB.
- The Dot booted **into TWRP recovery** before you start (how: see **Steps — in order** below).

## Steps — in order

1. **Put the Dot into TWRP recovery.**
   - *Button (no PC needed):* with power unplugged, hold **ONLY the Volume Up** button, apply
     power, and keep holding until the LED ring is **steady white** — release once recovery is
     up.
   - *From a PC:* boot hacked fastboot (hold **Volume Down**, rainbow LED) and run amonet's
     `fastboot-step.sh` — a known-working copy is kept in
     [`third_party/amonet-biscuit/`](third_party/amonet-biscuit/fastboot-step.sh)
     (`fastboot flash recovery bin/twrp.img && fastboot reboot recovery`).
   - Volume **Down** = hacked fastboot, **Mute** = USBDL — neither is TWRP, so hold only
     **Volume Up**. The add-on cannot trigger this step for you; it is manual.
2. **Move the Dot to the Home Assistant host.** With it still in TWRP (white LED), unplug it and
   plug it into this host's USB port **while holding the Volume Up button** — it powers up back
   into TWRP on this host.
3. **Open the EchoLocal Installer panel** (install the add-on first — see **Install** below),
   start it and open the UI, then press **Refresh**: the Dot should list with state `recovery`.
4. **Install.** Pick the device, enter a **name** (Home Assistant keys the device on this name)
   and your **Wi-Fi** details, then press **Install** and watch the live log. Leave TWRP alone
   until it finishes.
5. **Done.** Home Assistant discovers the Dot through ESPHome; the panel shows the pairing key
   (or the zero-PSK note) when there is one.

> Full walkthrough including the one-time unlock:
> [docs/unlocking.md](docs/unlocking.md).
> `adb reboot recovery` is a software path, but it works only *after* EchoLocal is installed
> (rooted Android with adb authorized to this add-on) — never for the first install.

> The add-on is not tested against every HAOS host. If `adb` cannot see the Dot, see
> **Troubleshooting** below.

## Install

1. In Home Assistant: **Settings → Add-ons → Add-on Store → ⋮ → Repositories**.
2. Add:

   ```
   https://github.com/MJP-76/echolocal-ha-addon
   ```

3. Find **EchoLocal Installer** in the store and install it.
4. Start it, then open it from the sidebar (or **Open Web UI**).

## How it works

- `config.yaml` maps USB (`usb: true`), the host udev database (`udev: true`) and an Ingress
  panel on port 8099.
- The image is `alpine` plus `android-tools` (so `adb`/`fastboot` exist) and `python3`.
- On first run the add-on downloads the pinned `echoctl` Linux build for the host architecture
  from the upstream GitHub release and verifies it against that release's `checksums.txt`.
- The web UI lists devices with `adb devices -l` and runs
  `echoctl install --serial … --name … -y` with the Wi-Fi flags you supply. `echoctl` prints
  plain progress lines when its stdout is a pipe, which is exactly how it is run here.

### The recovery workaround

`echoctl` 0.0.8 aborts on Fire OS 6 when `/system_root/vendor` is a dangling symlink whose
target has no `etc/init/*.rc`, because a non-matching shell glob makes `ls` exit non-zero and
the installer treats that as fatal (upstream issue
[#94](https://github.com/ygelfand/echolocal/issues/94)).

Before invoking `echoctl`, the add-on creates a throwaway placeholder in TWRP
(`/system/vendor/etc/init/echolocal-placeholder.rc`) so the glob matches. It is RAM-only and
disappears when the device reboots. This is removed as soon as a fixed `echoctl` release is
pinned. See `docs/development/`.

## Troubleshooting

- **No device detected.** Confirm the Dot is in TWRP and the USB cable carries data (not a
  charge-only cable). Check the add-on log for `adb` errors.
- **`adb` sees nothing.** Some hosts need the add-on to have full device access. Enable
  **Protection mode off** in the add-on page, then in the add-on configuration set
  `full_access: true` (this maps all host devices in, and is broader than `usb: true`).
- **Install stops at `selinux permissive` or `device name`.** The
  `vendor/etc/init` workaround did not take. Re-run with the Dot freshly booted into TWRP.
- **Wi-Fi step fails.** For a secured network you must supply the passphrase; leaving it blank
  joins with an empty password and fails. An SSID left blank only works when the Dot is
  already connected to (or has saved) a network.

## Credits

All of the hard work is [ygelfand/echolocal](https://github.com/ygelfand/echolocal). This
repository is only an installer front-end.
