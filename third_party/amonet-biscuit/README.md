# amonet-biscuit: fastboot-step.sh (vendored)

Verbatim copy of `fastboot-step.sh` from the amonet `mt8163-biscuit` branch
(Rortiz2 / k4y0z, [R0rt1z2/amonet](https://github.com/R0rt1z2/amonet)), kept in this
repository because it is the known-working way to put an unlocked Dot into TWRP.

For EchoLocal, this is the only amonet script this project needs — the rest of the
XDA article (FireOS re-flash, A/B slot switching, boot-root) is not required.

## What it does

```sh
fastboot flash recovery bin/twrp.img
fastboot reboot recovery
```

Flashes the TWRP recovery image to the Dot and reboots it straight into recovery.

## When to use it

- The Dot must be **already unlocked** (hacked bootloader, amonet unlock done once).
- Boot the Dot into **hacked fastboot**: hold **Volume Down** and apply power → rainbow LED.

## How to run it

Run it from inside the extracted `amonet-biscuit-*.zip` release folder, so the
`bin/fastboot` and `bin/twrp.img` files it needs are present next to it
(alternatively drop this script into that folder):

```sh
./fastboot-step.sh
```

## Provenance

- Upstream: https://github.com/R0rt1z2/amonet/blob/mt8163-biscuit/fastboot-step.sh
- Vendored at commit/pin: copied from the `mt8163-biscuit` branch, October 2026.
- SHA-256 of this file: see `sha256sum fastboot-step.sh` after checkout (regenerated
  on first vendor, recorded below for verification).

```text
f529e48a20af265e96a6dbac5d7a6d4ad8e112785ee720b99f1624ebe5c2bd0c
```

- License: upstream repository is MIT / GPL-2.0 overall; this script is the trivial
  two-command wrapper from that project. See the upstream LICENSE files.