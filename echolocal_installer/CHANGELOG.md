# Changelog

## 0.1.2 — 2026-10-09

- Document the final pairing step (copy the key → Settings → Devices & Services → ESPHome →
  Configure → paste the encryption key) in the panel, README, and DOCS.md.

## 0.1.1 — 2026-10-09

- Fix the install POST body being lost through Home Assistant's ingress proxy (it uses chunked
  transfer encoding; the server only read Content-Length bodies), which made every panel install
  fail with "no device selected" regardless of the selected device.

## 0.1.0 — 2026-10-09

Initial release.

- Ingress panel that lists USB devices with `adb` and runs a pinned `echoctl install` with
  live log streaming.
- Downloads the pinned `echoctl` release binary for the host architecture and verifies the
  SHA-256 against the release's `checksums.txt`.
- Automatic TWRP `vendor/etc/init` placeholder workaround for the upstream `initRC` glob bug
  (issue #94); removed once a fixed `echoctl` release is pinned. See
  `docs/development/upstream-initrc-fix.md`.
- Installer only: no Wi-Fi reconfiguration, no uninstall, no entities.