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
  **one-time PC step** — for an EchoLocal install **nothing else from the unlock guide is
  needed** (no FireOS re-flash, no root). Full flow:
  [docs/unlocking.md](docs/unlocking.md) · [XDA thread](https://xdaforums.com/t/unlock-root-twrp-unbrick-amazon-echo-dot-2nd-gen-2016-biscuit.4761416/).
- The Dot connected to the Home Assistant host by USB.
- The Dot booted **into TWRP recovery** before you start (how: see **Steps — in order** below).

## Steps — in order

1. **Unlock the Dot first — one-time, on a Windows/Linux PC** (skip this step if the Dot is
   already unlocked):
   - Download the latest **amonet-biscuit** package from the
     [XDA thread](https://xdaforums.com/t/unlock-root-twrp-unbrick-amazon-echo-dot-2nd-gen-2016-biscuit.4761416/)
     (reference for the full procedure) and extract it.
   - Connect the Dot to the PC with a data USB cable. Unplug its power, then reconnect it
     **while holding the action button** (the dot — "•") until the ring glows **green**
     (Amazon factory fastboot). Release.
   - Run **`fastbrick.sh`** (Linux, in a terminal inside the extracted folder) or
     **`fastbrick.bat`** (Windows, double-click). A known-working copy of the shell script is
     kept in this repo: [`third_party/amonet-biscuit/fastbrick.sh`](third_party/amonet-biscuit/fastbrick.sh).
     **Type `YES`** when prompted and follow the on-screen instructions.
   - **DO NOT INTERRUPT THE PROCESS AFTER THE 10-SECOND GRACE PERIOD — ANY INTERRUPTION BRICKS
     THE DEVICE.** Watch the LEDs — the ring shows progress.
   - Wait up to a minute: the ring turns green again and the Dot **reboots into TWRP —
     steady white ring**.
2. **Move the Dot to the Home Assistant host.** It is sitting in TWRP (white ring) from step 1
   (or, if it has been rebooted since, enter TWRP first — hold **ONLY the Volume Up** button
   and apply power until the white ring appears). Unplug it and plug it into this host's USB
   port **while holding the Volume Up button until the white ring comes back** — the Dot is now
   in TWRP on this host.
3. **Open the EchoLocal Installer panel** (install the add-on first — see **Install** below),
   start it and open the UI, then press **Refresh**: the Dot should list with state `recovery`.
4. **Install.** Pick the device, enter a **name** (Home Assistant keys the device on this name)
   and your **Wi-Fi** details, then press **Install** and watch the live log. Leave TWRP alone
   until it finishes.
5. **Add the Dot in Home Assistant.** When the install finishes, the panel shows the
   **pairing (encryption) key** — copy it. Then open **Settings → Devices & Services →
   ESPHome**: the freshly installed Dot (e.g. *Lounge DOT*) appears as a discovered device —
   press **Configure** on it (or **Add Device** and enter the Dot's IP address) and
   **paste the encryption key** into the config flow to finish pairing. If the panel showed a
   zero-PSK note instead of a key, choose the zero-PSK / push-key option. Home Assistant then
   creates the device and its entities.

> **Boot modes after the unlock:** Volume **Up** = TWRP (white ring) · Volume **Down** = hacked
> fastboot (rainbow) · **Mute** = USBDL (no LED). Only Volume Up matters here; the add-on cannot
> trigger TWRP entry, it is always manual. From a PC, amonet's
> [`fastboot-step.sh`](third_party/amonet-biscuit/fastboot-step.sh) (kept in this repo — known
> to work) can also flash TWRP and boot recovery from hacked fastboot.

> Full walkthrough: [docs/unlocking.md](docs/unlocking.md).
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
