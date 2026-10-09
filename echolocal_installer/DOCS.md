# EchoLocal Installer

An add-on that flashes and installs [EchoLocal](https://github.com/ygelfand/echolocal) onto an
unlocked 2nd-generation Amazon Echo Dot, over USB, from a Home Assistant sidebar panel.

## Prerequisites

The add-on **cannot unlock** a device. The Dot must already be:

- unlocked with the amonet-biscuit procedure (TWRP as recovery), **and**
- powered on into **TWRP recovery**, **and**
- connected to this Home Assistant host with a USB cable that carries data.

## Configuration

| Option | Default | Description |
| --- | --- | --- |
| `echoctl_version` | `0.0.8` | Version of the upstream `echoctl` binary to download and run. Keep pinned at the tested version; bump only after verifying a new release works. 0.0.8 is the correct version for SDK 25 (Fire OS 6). |

The add-on downloads the pinned `echoctl` Linux build for the host architecture at first use and
verifies its SHA-256 against the release's `checksums.txt`. The binary and adb keys persist in
`/data` so a rebuild does not invalidate device trust.

## Using it

1. Put the Dot into TWRP recovery, connect it by USB, and open the **EchoLocal Installer** panel.
2. Press **Refresh** and pick the device. It should list with state `recovery`.
3. Enter a name and your Wi-Fi details, then press **Install**.
4. Watch the log. When it finishes, Home Assistant discovers the device via ESPHome; the panel
   shows the pairing key if one was generated, or notes zero-PSK provisioning if not.

## Notes

- **Installer only.** The add-on does not change Wi-Fi afterwards, reinstall, uninstall, or add
  any entities.
- **Workaround for upstream issue #94.** Before flashing, the add-on creates a RAM-only
  placeholder at `/system/vendor/etc/init/echolocal-placeholder.rc` in TWRP so that a dangling
  `/system_root/vendor` symlink does not make `echoctl` abort while it lists init rc files. This
  disappears on reboot and is removed from the add-on once a fixed `echoctl` release is pinned.

## Troubleshooting

- **No device detected** — confirm TWRP recovery and a data-capable cable. For some hosts,
  enable **Protection mode off** and set the add-on option `full_access: true` instead of
  relying on `usb: true`.
- **Install stops at `selinux permissive` or `device name`** — the workaround did not take.
  Reboot the Dot fresh into TWRP and run Install again.
- **Wi-Fi fails** — for a secured network the passphrase is required; a blank one joins with an
  empty password. A blank SSID only works when the Dot is already connected to a network.

## Support

The underlying tool is upstream: [ygelfand/echolocal](https://github.com/ygelfand/echolocal).
Issues about this installer belong in
[this repository](https://github.com/MJP-76/echolocal-ha-addon).