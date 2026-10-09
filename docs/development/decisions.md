# Decisions

Record of why this repository is the way it is. Newest last.

## D1 — An add-on, not an integration (2026-10-09)

Flashing an Echo Dot needs raw USB and `adb`. A Home Assistant **integration** runs in the
Core container, which has no USB access; a Supervisor **add-on** can request `usb: true`.
So the installer is an add-on with an Ingress panel.

Consequence: Home Assistant cannot "figuring out the USB side" for us unless it can see
`/dev/bus/usb`, which only the add-on can.

## D2 — Install only (2026-10-09)

The add-on installs EchoLocal and stops there. No Wi-Fi reconfiguration, no status polling,
no uninstall, and **no entities or devices registered in Home Assistant**. Adding a companion
integration later would be a separate decision.

## D3 — Pin `echoctl` to 0.0.8 (2026-10-09)

The add-on downloads the upstream `echoctl` release binary rather than embedding it, so it can
be bumped without rebuilding. 0.0.8 is the version this add-on is written and tested against;
the version is an add-on option (`echoctl_version`) so a future fix can be adopted without a
code change. Do **not** downgrade to 0.0.6 — 0.0.8 is the correct version for SDK 25.

## D4 — Carry the TWRP workaround until upstream is fixed (2026-10-09)

`echoctl` 0.0.8 aborts on Fire OS 6 when a shell glob matches nothing: `/system_root/vendor` is
an absolute symlink to `/system/vendor`, which in TWRP resolves into an empty rootfs, so
`vendor/etc/init/*.rc` matches nothing, `ls` exits non-zero, and the installer treats that as
fatal (upstream issue #94). Until a fixed `echoctl` is released and pinned, the add-on creates
a RAM-only placeholder at `/system/vendor/etc/init/echolocal-placeholder.rc` in TWRP before
invoking `echoctl`. **Remove this workaround when the fixed release is pinned** (see
`upstream-initrc-fix.md`).

## D5 — Do not fork upstream (2026-10-09)

The bug is a one-line fix upstream. Forking `echoctl` would mean carrying a divergent binary
and losing upstream fixes. Instead the fix is proposed upstream (patch + issue #94 comment in
`upstream-initrc-fix.md`) and, in the meantime, the add-on works around it.

## D6 — `alpine` + `android-tools` + stdlib Python (2026-10-09)

The image is plain `alpine:3.21` with `python3` and `android-tools` (which ships `/usr/bin/adb`)
rather than the s6-based Home Assistant base image. The server is Python's stdlib only, so there
is no `pip` step and nothing to keep patched. `android-tools` was verified to provide `adb` on
Alpine 3.21.
