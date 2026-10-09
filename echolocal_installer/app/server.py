#!/usr/bin/env python3
"""EchoLocal Installer — Home Assistant ingress app that flashes an Echo Dot over USB.

The heavy lifting is done by echoctl (https://github.com/ygelfand/echolocal), which this app
downloads from its release channel and runs non-interactively. echoctl prints plain progress
lines when its stdout is not a terminal, which is exactly how it is run here.

The app is deliberately smarted-free: it lists devices with `adb devices -l`, asks for a name
and Wi-Fi details, and streams one `echoctl install` run to the browser over SSE.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import queue
import subprocess
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = 8099
APP_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(APP_DIR, "static")

DATA_DIR = "/data"
BIN_DIR = os.path.join(DATA_DIR, "bin")
ECHOCTL = os.path.join(BIN_DIR, "echoctl")
VERSION_STAMP = os.path.join(BIN_DIR, "echoctl.version")
OPTIONS_FILE = os.path.join(DATA_DIR, "options.json")

REPO = "ygelfand/echolocal"
ASSET_BY_MACHINE = {
    "x86_64": "echolocal_linux_x86_64",
    "amd64": "echolocal_linux_x86_64",
    "aarch64": "echolocal_linux_arm64",
    "arm64": "echolocal_linux_arm64",
}

# The add-on container is rebuilt from scratch, but /data persists. adb must keep one identity
# across restarts, so its key lives on the persistent volume.
ADB_HOME = os.path.join(DATA_DIR, ".android")

# TWRP RAM-only placeholder for upstream issue #94 (dangling /system_root/vendor symlink).
# Remove together with apply_vendor_workaround once a fixed echoctl is pinned.
WORKAROUND_RC = "echolocal-placeholder.rc"


def adb_env():
    env = os.environ.copy()
    env["HOME"] = DATA_DIR
    env["ANDROID_USER_HOME"] = ADB_HOME
    return env


class Hub:
    """Stores the current install log and fans events out to SSE subscribers."""

    def __init__(self):
        self._lock = threading.Lock()
        self._subs = []
        self.log = []
        self.status = "idle"
        self.result = {}
        self.busy = False
        self.last_error = ""

    def subscribe(self):
        with self._lock:
            q = queue.Queue()
            backlog = list(self.log)
            status = {"kind": "status", "status": self.status, **self.result}
            self._subs.append(q)
            return q, backlog, status

    def unsubscribe(self, q):
        with self._lock:
            if q in self._subs:
                self._subs.remove(q)

    def _publish(self, event):
        with self._lock:
            subs = list(self._subs)
        for q in subs:
            try:
                q.put_nowait(event)
            except Exception:
                pass

    def log_line(self, line):
        line = str(line).rstrip("\n")
        if not line:
            return
        with self._lock:
            self.log.append(line)
            if len(self.log) > 8000:
                del self.log[: len(self.log) - 8000]
        self._publish({"kind": "log", "line": line})

    def set_status(self, status, **extra):
        with self._lock:
            self.status = status
            self.result.update(extra)
            self.busy = status == "running"
            if status == "failed" and "error" in extra:
                self.last_error = extra["error"]
        self._publish({"kind": "status", "status": self.status, **self.result})


hub = Hub()
_download_lock = threading.Lock()


# ------------------------------------------------ options / state ----------------
def read_options():
    try:
        with open(OPTIONS_FILE, encoding="utf-8") as fh:
            return json.load(fh)
    except Exception:
        return {}


def pinned_version():
    return str(read_options().get("echoctl_version", "0.0.8"))


def installed_version():
    try:
        with open(VERSION_STAMP, encoding="utf-8") as fh:
            return fh.read().strip()
    except OSError:
        return ""


def echoctl_ready(version):
    if not (os.path.isfile(ECHOCTL) and os.access(ECHOCTL, os.X_OK)):
        return False
    if installed_version() != version:
        return False
    return True


# ------------------------------------------------ download -------------------------
def http_get(url, timeout=180):
    req = urllib.request.Request(url, headers={"User-Agent": "echolocal-installer-addon/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return resp.read()


def verify_checksum(asset, data, checksums):
    want = None
    for line in checksums.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1].lstrip("*") == asset:
            want = parts[0].lower()
            break
    if want is None:
        raise RuntimeError(f"{asset} is not listed in checksums.txt")
    got = hashlib.sha256(data).hexdigest()
    if got != want:
        raise RuntimeError(f"checksum mismatch for {asset}")


def ensure_echoctl(version):
    """Download and verify the pinned echoctl binary exactly once per version."""
    with _download_lock:
        if echoctl_ready(version):
            return
        machine = platform.machine()
        asset = ASSET_BY_MACHINE.get(machine)
        if not asset:
            raise RuntimeError(f"no echoctl build for architecture {machine!r}")
        base = f"https://github.com/{REPO}/releases/download/{version}"
        hub.log_line(f"Downloading {asset} ({version}) …")
        data = http_get(f"{base}/{asset}")
        try:
            sums = http_get(f"{base}/checksums.txt").decode("utf-8", "replace")
            verify_checksum(asset, data, sums)
            hub.log_line("Checksum verified against checksums.txt.")
        except Exception as exc:  # noqa: BLE001 - surface but do not block a user fix
            hub.log_line(f"WARNING: could not verify checksum: {exc}")
        os.makedirs(BIN_DIR, exist_ok=True)
        tmp = ECHOCTL + ".part"
        with open(tmp, "wb") as fh:
            fh.write(data)
        os.chmod(tmp, 0o755)
        os.replace(tmp, ECHOCTL)
        with open(VERSION_STAMP, "w", encoding="utf-8") as fh:
            fh.write(version)
        hub.log_line(f"Installed echoctl {version}.")


def _download_thread(version):
    try:
        ensure_echoctl(version)
    except Exception as exc:  # noqa: BLE001 - an install will surface this again
        hub.log_line(f"Download failed: {exc}")


# ------------------------------------------------ adb ------------------------------
def adb_devices():
    proc = subprocess.run(
        ["adb", "devices", "-l"],
        capture_output=True, text=True, env=adb_env(), timeout=30,
    )
    devices = []
    for raw in proc.stdout.splitlines()[1:]:
        line = raw.strip()
        if not line:
            continue
        parts = line.split()
        if len(parts) < 2:
            continue
        serial, state = parts[0], parts[1]
        attrs = {}
        for token in parts[2:]:
            if ":" in token:
                key, _, value = token.partition(":")
                attrs[key] = value
        devices.append({
            "serial": serial,
            "state": state,
            "model": attrs.get("model", ""),
            "product": attrs.get("product", ""),
            "device": attrs.get("device", ""),
        })
    return devices


def adb_shell(serial, script, timeout=30):
    proc = subprocess.run(
        ["adb", "-s", serial, "shell", script],
        capture_output=True, text=True, env=adb_env(), timeout=timeout,
    )
    return proc.stdout.strip(), proc.returncode


# ------------------------------------------------ workaround -----------------------
def apply_vendor_workaround(serial, state):
    if state != "recovery":
        hub.log_line("Device is not in recovery; skipping the vendor/etc/init workaround.")
        return
    hub.log_line("Applying the recovery vendor/etc/init workaround (echoctl issue #94) …")
    script = (
        "mkdir -p /system/vendor/etc/init 2>/dev/null; "
        f"touch /system/vendor/etc/init/{WORKAROUND_RC} 2>/dev/null; "
        "ls /system/vendor/etc/init/*.rc 2>/dev/null | head -n 1"
    )
    out, _ = adb_shell(serial, script)
    if out:
        hub.log_line(f"  vendor/etc/init now holds: {out.splitlines()[-1]}")
    else:
        hub.log_line("  could not confirm a placeholder; the install may stop at 'selinux permissive'.")


# ------------------------------------------------ install --------------------------
def redact(argv):
    """Do not put the Wi-Fi passphrase in the log."""
    out, hide = [], False
    for token in argv:
        if hide:
            out.append("********")
            hide = False
            continue
        out.append(token)
        if token == "--password":
            hide = True
    return out


def build_install_cmd(serial, name, ssid, password, reboot):
    cmd = [ECHOCTL, "install", "--serial", serial, "-y"]
    cmd.append("--reboot" if reboot else "--no-reboot")
    if name:
        cmd += ["--name", name]
    if ssid:
        cmd += ["--ssid", ssid]
        if password:
            cmd += ["--password", password]
    return cmd


def read_key(serial):
    """Read the pairing key after install; empty means the device is unprovisioned (zero-PSK)."""
    for args in (["key", "show"], ["key"]):
        try:
            proc = subprocess.run(
                [ECHOCTL, *args, "--serial", serial],
                capture_output=True, text=True, env=adb_env(), timeout=60,
            )
        except Exception:  # noqa: BLE001
            continue
        if proc.returncode == 0 and proc.stdout.strip():
            out = proc.stdout.strip()
            if "unprovisioned" in out:
                return ""
            lines = [ln for ln in out.splitlines() if ln.strip()]
            if lines:
                return lines[-1]
    return ""


def run_install(payload):
    try:
        version = payload.get("version") or pinned_version()
        serial = (payload.get("serial") or "").strip()
        if not serial:
            raise RuntimeError("no device selected")
        reboot = bool(payload.get("reboot", True))
        name = (payload.get("name") or "").strip()
        ssid = (payload.get("ssid") or "").strip()
        password = payload.get("password") or ""

        hub.log_line("Starting adb server …")
        subprocess.run(["adb", "start-server"], capture_output=True, text=True,
                       env=adb_env(), timeout=30)

        known = {dev["serial"]: dev for dev in adb_devices()}
        dev = known.get(serial)
        if dev is None:
            raise RuntimeError(f"device {serial} is no longer connected")
        if dev["state"] not in ("device", "recovery"):
            raise RuntimeError(f"device {serial} is {dev['state']}; echoctl needs it 'device' or 'recovery'")

        ensure_echoctl(version)
        apply_vendor_workaround(serial, dev["state"])

        cmd = build_install_cmd(serial, name, ssid, password, reboot)
        hub.log_line("$ " + " ".join(redact(cmd)))
        hub.log_line("")

        proc = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1, env=adb_env(),
        )
        for line in proc.stdout:
            hub.log_line(line.rstrip("\n"))
        code = proc.wait()

        if code != 0:
            hub.log_line(f"echoctl exited with status {code}.")
            hub.set_status("failed", exit=code, key="")
            return

        key = read_key(serial)
        hub.log_line("")
        if key:
            hub.log_line("Pairing key: " + key)
        else:
            hub.log_line("No key on the device (zero-PSK provisioning) — Home Assistant can push one.")
        hub.set_status("done", exit=0, key=key)
    except Exception as exc:  # noqa: BLE001 - surfaced to the panel
        hub.log_line(f"ERROR: {exc}")
        hub.set_status("failed", exit=-1, key="", error=str(exc))


def start_install(payload):
    with hub._lock:
        if hub.busy:
            return False
        hub.log = []
        hub.status = "running"
        hub.result = {}
        hub.busy = True
        hub.last_error = ""
    hub._publish({"kind": "reset"})
    hub._publish({"kind": "status", "status": "running"})
    threading.Thread(target=run_install, args=(payload,), daemon=True).start()
    return True


# ------------------------------------------------ http ------------------------------
class Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "EchoLocalInstaller/0.1"

    def log_message(self, fmt, *args):  # keep the app log quiet
        pass

    def _send(self, code, body=b"", ctype="text/plain; charset=utf-8", extra=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        for key, value in (extra or {}).items():
            self.send_header(key, value)
        self.end_headers()
        if body:
            self.wfile.write(body)

    def _json(self, obj, code=200):
        self._send(code, json.dumps(obj).encode("utf-8"), "application/json")

    def _sse(self, obj):
        data = json.dumps(obj).encode("utf-8")
        self.wfile.write(b"data: " + data + b"\n\n")
        self.wfile.flush()

    def do_GET(self):
        path = self.path.split("?", 1)[0]
        if path in ("/", "/index.html"):
            try:
                with open(os.path.join(STATIC_DIR, "index.html"), "rb") as fh:
                    self._send(200, fh.read(), "text/html; charset=utf-8")
            except OSError:
                self._send(500, b"index.html missing", "text/plain; charset=utf-8")
        elif path == "/api/state":
            version = pinned_version()
            self._json({
                "status": hub.status,
                "busy": hub.busy,
                "echoctl_version": version,
                "binary_ready": echoctl_ready(version),
                "arch": platform.machine(),
                "devices": [] if hub.busy else adb_devices(),
                "result": hub.result,
            })
        elif path == "/api/devices":
            self._json({"devices": adb_devices()})
        elif path == "/api/events":
            self._events()
        else:
            self._send(404, b"not found")

    def do_POST(self):
        path = self.path.split("?", 1)[0]
        length = int(self.headers.get("Content-Length", 0) or 0)
        raw = self.rfile.read(length) if length else b""
        if path == "/api/install":
            try:
                payload = json.loads(raw or b"{}")
            except Exception:  # noqa: BLE001
                payload = {}
            if start_install(payload):
                self._json({"started": True})
            else:
                self._json({"started": False, "error": "an install is already running"}, 409)
        elif path == "/api/download":
            threading.Thread(target=_download_thread, args=(pinned_version(),), daemon=True).start()
            self._json({"started": True})
        else:
            self._send(404, b"not found")

    def _events(self):
        q, backlog, status = hub.subscribe()
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("Connection", "close")
        self.send_header("X-Accel-Buffering", "no")
        self.end_headers()
        self.close_connection = True
        try:
            self._sse(status)
            for line in backlog:
                self._sse({"kind": "log", "line": line})
            while True:
                try:
                    event = q.get(timeout=15)
                except queue.Empty:
                    self.wfile.write(b": ping\n\n")
                    self.wfile.flush()
                    continue
                self._sse(event)
        except (BrokenPipeError, ConnectionResetError):
            pass
        finally:
            hub.unsubscribe(q)


def main():
    os.makedirs(BIN_DIR, exist_ok=True)
    os.makedirs(ADB_HOME, exist_ok=True)
    version = pinned_version()
    hub.log_line("EchoLocal Installer ready.")
    hub.log_line(
        f"echoctl {version} ({'cached' if echoctl_ready(version) else 'not downloaded yet'})."
    )
    threading.Thread(target=_download_thread, args=(version,), daemon=True).start()

    server = ThreadingHTTPServer(("", PORT), Handler)
    server.daemon_threads = True
    print(f"EchoLocal Installer listening on :{PORT}", flush=True)
    server.serve_forever()


if __name__ == "__main__":
    main()