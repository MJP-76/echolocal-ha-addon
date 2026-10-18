# TODO

Single source of truth for outstanding work on this repository.

## Done

- [x] 2026-10-18 — Field test: two EchoMuse dots (emOS flow) converted via the add-on with
      **Clean previous install leftovers** ticked. On G090LF0964540AQS ("Reception2 DOT") the
      clean removed `/data/emos`, `/data/local/bin` and `/data/misc/wifi`; `/data/adb` absent
      as expected (emOS flow installs no Magisk); post-check clean. echoctl 12/12 + 16/16 + 3/3,
      Wi-Fi up (172.16.1.115), echod resident, key handled. The vendor placeholder was not
      confirmed on this build but the install passed 'selinux permissive' anyway. The log was
      only recovered after the fact — motivated the 0.1.4 rename sync and `/data/last-install.log`.
- [x] 2026-10-09 — End-to-end test on a fresh TWRP-unlocked Dot (G090LF0964540CET, "Lounge DOT"):
      `usb: true` passthrough works on this HAOS host; add-on installed EchoLocal in ~96 s
      (root 12/12, install 16/16, Wi-Fi up, echod resident after reboot, pairing key shown).
      Required the 0.1.1 fix for install POST bodies lost through HA ingress (the ingress
      proxy sends chunked transfer encoding; the server previously read only Content-Length).

## Now

- [ ] File the upstream fix for the `initRC` glob bug (issue #94) — patch and comment are
      drafted in `docs/development/upstream-initrc-fix.md`.

## Soon

- [ ] Drop the TWRP `vendor/etc/init` workaround once a fixed `echoctl` release is pinned.
      (Needed on Dot #1 G090LF09645406G2; NOT needed on Dot #2 G090LF0964540CET — keep it
      until a fixed release is pinned, then remove server.py's `apply_vendor_workaround`.)
- [ ] Add `icon.png` and `logo.png` to `echolocal_installer/`.
- [ ] Surface the post-install `echoctl status` output in the panel.

## Later

- [ ] Convenience: a "boot to recovery" button using `adb reboot recovery` for Dots already
      running rooted Android with adb authorized to this add-on — never for the first install,
      which stays a manual button combo (README, "Entering TWRP").
- [ ] Optional: re-configure Wi-Fi without a full re-install (upstream issue #83).
- [ ] Optional: expose install progress to automations (would need a companion integration).
