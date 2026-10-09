# TODO

Single source of truth for outstanding work on this repository.

## Now

- [ ] Test the add-on end to end on a fresh, TWRP-unlocked Echo Dot and confirm `usb: true`
      passthrough works on this HAOS host.
- [ ] File the upstream fix for the `initRC` glob bug (issue #94) — patch and comment are
      drafted in `docs/development/upstream-initrc-fix.md`.

## Soon

- [ ] Drop the TWRP `vendor/etc/init` workaround once a fixed `echoctl` release is pinned.
- [ ] Add `icon.png` and `logo.png` to `echolocal_installer/`.
- [ ] Surface the post-install `echoctl status` output in the panel.

## Later

- [ ] Optional: re-configure Wi-Fi without a full re-install (upstream issue #83).
- [ ] Optional: expose install progress to automations (would need a companion integration).
