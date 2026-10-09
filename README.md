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
- An Echo Dot **already unlocked, with TWRP as its recovery** — the amonet-biscuit unlock,
  [Option 1, no disassembly on a working Dot](docs/unlocking.md): unplug power, hold the
  **action button** (the dot — "•"), plug power back in → **green** LED (factory fastboot),
  then run `fastbrick` from a PC and flash FireOS 6 to both slots. This add-on does **not**
  run the exploit; it takes over once the device is unlocked and booted into TWRP.
- The Dot connected to the Home Assistant host by USB.
- The Dot booted **into TWRP recovery** before you start (how: see **Entering TWRP** below).

### Entering TWRP (before each install)

On an unlocked biscuit the volume buttons are the boot-mode selector (amonet v2.0+):

- **TWRP / recovery** — hold **ONLY the Volume Up** button and apply power. Keep holding until
  the LED ring shows a **steady white**, then release.
- Hacked **fastboot** — hold **ONLY Volume Down** and apply power (**rainbow** LED). Only needed
  to re-run parts of the unlock.
- **USBDL** (preloader, for unbricking) — hold the **Mute** button and apply power with USB
  connected; there is **no LED**. This is *not* TWRP — hold Mute and you will *not* see recovery.

Entering TWRP is always a manual step; the add-on cannot trigger it. `adb reboot recovery` is
a software path, but it works only while the Dot is already running Android with adb
authorized to this add-on's key — i.e. only *after* EchoLocal is installed. It is a later
convenience, not a first-install path, and this add-on does not offer it yet. From a PC, amonet's
`fastboot-step.sh` can also flash TWRP and boot recovery directly from hacked fastboot (see
[docs/unlocking.md](docs/unlocking.md)).

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

## Use

1. Boot the Dot into TWRP recovery (see **Entering TWRP** above: hold **Volume Up**, apply
   power, steady white LED), and connect it by USB.
2. In the panel, press **Refresh** and pick the device. It should show state `recovery`.
3. Fill in a **name** (Home Assistant keys the device on this name) and your **Wi-Fi**
   details, then press **Install**.
4. Watch the live log. When it finishes, Home Assistant will discover the device through
   ESPHome. The panel shows the pairing key (or the zero-PSK note) when there is one.

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
