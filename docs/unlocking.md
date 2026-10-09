# Unlocking a Dot — amonet-biscuit, Option 1

Condensed (with permission wording kept) from the XDA guide by **Rortiz2**:

https://xdaforums.com/t/unlock-root-twrp-unbrick-amazon-echo-dot-2nd-gen-2016-biscuit.4761416/

Read that thread before starting — this page is a convenience copy of **Option 1** for a Dot
that **still boots**. amonet **v2.0.0+** only; FireOS 5 will not boot on v2.0 unlocks.

## ⚠️ Warnings

- **This is for the 2nd-gen Echo Dot (biscuit), 2016, model RS03QR only.**
- The process carries a **significant risk of permanently bricking** the device if anything
  goes wrong. Proceed entirely at your own risk.
- **DO NOT INTERRUPT THE PROCESS AFTER THE 10-SECOND GRACE PERIOD — ANY INTERRUPTION WILL
  BRICK THE DEVICE.**
- Never modify the bootloader or critical partitions (LK, Preloader, TZ) afterwards — that
  permanently bricks the Dot with no recovery.

## What you need (Option 1)

- A Windows or Linux computer (the exploit runs on the PC, not in Home Assistant).
- A MicroUSB cable that carries data, to connect the Dot to that PC.
- Windows only: install the [Kindle Fire driver](https://developer.amazon.com/docs/fire-tablets/connecting-adb-to-device.html#install_usb_driver)
  (or [Google's USB driver for ADB & Fastboot](https://developer.android.com/studio/run/win-usb)).

> If your Dot is **already unlocked** and you just want to update amonet to a newer release,
> flash the current `amonet-biscuit-vX.zip` in TWRP — do **not** re-run fastbrick.
> If your Dot is **bricked** and cannot reach fastboot, use **Option 2** from the thread
> (disassemble, short a test point to GND while running `bootrom-step.sh`) — not covered here.

## Steps

1. **Get amonet.** Download the latest `amonet-biscuit-v2.0.0.zip` from the thread's
   attachments and extract it.
2. **Start fastbrick.** Open a terminal in the extracted folder:
   - Windows: double-click `fastbrick.bat`
   - Linux: `./fastbrick.sh`
3. **Enter factory fastboot.** Unplug the power cable, then reconnect it **while holding the
   action button** (the circle, "•"). Keep holding until the LED ring glows **green** — that is
   Amazon's factory fastboot mode. Release.
4. **Run the exploit.** The script detects the device; **type `YES`** when prompted. Follow all
   on-screen instructions and watch the LEDs — the ring shows progress. **After the 10-second
   grace period, do not touch or interrupt anything.** Wait up to 1 minute.
5. **Result.** The LED turns green again and the device **reboots into TWRP (steady white LED)**.
6. **Flash FireOS 6 before it can boot.** The Dot uses an **A/B partitioning scheme**, so the
   ROM must be installed to **both slots**. Get the latest FireOS 6 build for biscuit from
   [FTVDB](https://ftvdb.com/echo/firmware/com.amazon.biscuit.android.os/) (e.g. the NS65741
   build — the `bcbtool` line switches to the unused slot):

   ```bash
   adb shell twrp wipe cache
   adb shell twrp wipe data
   adb push update-kindle-biscuit_puffin-NS65741_user_8142_0013222530692.bin /sdcard/update.zip
   adb shell twrp install /sdcard/update.zip
   adb shell 's=$(bcbtool get_active); case $s in a) bcbtool set_active b;; b) bcbtool set_active a;; *) echo "unexpected: $s";; esac'
   adb reboot recovery
   adb shell twrp install /sdcard/update.zip
   ```

7. **(Optional) Root and force ADB.** While still in TWRP:

   ```bash
   adb push boot-root.zip /sdcard/
   adb shell twrp install /sdcard/boot-root.zip
   adb reboot
   ```

   > If ADB does not show up after the reboot, power-cycle the device.

## After the unlock

- The Dot boots FireOS 6 with **TWRP as recovery** — it is now ready for the EchoLocal
  Installer add-on (see the [README](../README.md)).
- **Enter TWRP anytime:** hold **ONLY the Volume Up** button and apply power → **steady white**
  LED (release once recovery is up).
- **Fastboot route (from a PC):** boot hacked fastboot (hold **Volume Down**, rainbow LED), then
  run amonet's [`fastboot-step.sh`](https://github.com/R0rt1z2/amonet/blob/mt8163-biscuit/fastboot-step.sh)
  — it flashes `bin/twrp.img` and reboots the Dot straight into TWRP:
  `fastboot flash recovery bin/twrp.img && fastboot reboot recovery`.
- Volume **Down** alone = hacked fastboot (rainbow LED); **Mute** = USBDL/preloader mode, for
  unbricking with MTKClient (no LED) — not TWRP.
- TWRP is command-line only: `twrp install <zip>`, `twrp wipe data`, `twrp format data`,
  `twrp sideload`, `twrp reboot [recovery|poweroff|bootloader|download]`.
- **Replacing the base OS**: the stock FireOS 6 image can be re-flashed in TWRP to both slots
  (step 6 above — firmware from
  [FTVDB](https://ftvdb.com/echo/firmware/com.amazon.biscuit.android.os/)); this add-on instead
  replaces it with [EchoLocal](https://github.com/ygelfand/echolocal), a pure-Go rewrite of
  Amazon's services that Home Assistant discovers like any ESPHome device.

## Source

- Thread: https://xdaforums.com/t/unlock-root-twrp-unbrick-amazon-echo-dot-2nd-gen-2016-biscuit.4761416/
- Exploit: https://github.com/R0rt1z2/amonet (branch `mt8163-biscuit`) — unlock runs
  `fastbrick.sh`; `fastboot-step.sh` flashes TWRP and boots recovery, `boot-recovery.sh` boots
  recovery from a preloader handshake.
- TWRP device tree: https://github.com/R0rt1z2/twrp_device_amazon_biscuit