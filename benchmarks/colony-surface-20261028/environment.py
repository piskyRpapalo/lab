#!/usr/bin/env python3
"""Record scrubbed hardware, runtime, and endpoint counts for B1."""
import json
import platform
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path


def output(argv):
    try:
        result = subprocess.run(argv, check=True, text=True, capture_output=True, timeout=10)
        return result.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return None


def android_profile():
    version = output(["adb", "shell", "getprop", "ro.build.version.release"])
    abi = output(["adb", "shell", "getprop", "ro.product.cpu.abi"])
    mem = output(["adb", "shell", "cat", "/proc/meminfo"])
    total = re.search(r"^MemTotal:\s+(\d+) kB", mem or "", re.M)
    cores = output(["adb", "shell", "getconf", "_NPROCESSORS_ONLN"])
    size = output(["adb", "shell", "wm", "size"])
    density = output(["adb", "shell", "wm", "density"])
    refresh = output(["adb", "shell", "dumpsys", "display"])
    try:
        import urllib.request
        browser = json.load(urllib.request.urlopen("http://127.0.0.1:9222/json/version", timeout=3))
    except (OSError, ValueError):
        browser = {}
    rates = sorted({float(x) for x in re.findall(r"refreshRate[=: ]+(\d+(?:\.\d+)?)", refresh or "")})
    ready = output(["adb", "devices"])
    ready_count = sum(bool(line.strip().endswith("device")) for line in (ready or "").splitlines()[1:])
    usb = output(["lsusb"])
    usb_mobile_count = sum(
        bool(re.search(r"Apple, Inc\.|vivo|Samsung Electronics", line, re.I))
        for line in (usb or "").splitlines()
    )
    screen = re.search(r"Physical size:\s*(\d+x\d+)", size or "")
    dpi = re.search(r"Physical density:\s*(\d+)", density or "")
    return {
        "alias": "android-handset",
        "reachability": "ADB online",
        "os_version": version or "NO_DATA (Android property unavailable)",
        "cpu_abi": abi or "NO_DATA (Android property unavailable)",
        "online_cpu_cores": int(cores) if cores and cores.isdigit() else None,
        "memory_total_bytes": int(total.group(1)) * 1024 if total else None,
        "physical_screen_px": screen.group(1) if screen else None,
        "screen_density_dpi": int(dpi.group(1)) if dpi else None,
        "reported_refresh_rates_hz": rates or None,
        "browser_version": browser.get("Browser"),
        "adb_online_device_count": ready_count,
        "additional_usb_mobile_device_count_without_adb": usb_mobile_count,
        "device_serial": "OMITTED (SCRUB)",
        "device_product_name": "OMITTED (SCRUB)",
        "source_commands": [
            "adb shell getprop ro.build.version.release",
            "adb shell getprop ro.product.cpu.abi",
            "adb shell cat /proc/meminfo",
            "adb shell getconf _NPROCESSORS_ONLN",
            "adb shell wm size",
            "adb shell wm density",
            "adb shell dumpsys display",
            "adb devices",
            "lsusb (mobile-device class only; names and IDs discarded)",
            "Android Chrome DevTools version endpoint",
        ],
    }


def rack_profile():
    lscpu = output(["lscpu"])
    cpu = re.search(r"^Model name:\s*(.+)$", lscpu or "", re.M)
    logical = re.search(r"^CPU\(s\):\s+(\d+)$", lscpu or "", re.M)
    mem = output(["cat", "/proc/meminfo"])
    total = re.search(r"^MemTotal:\s+(\d+) kB", mem or "", re.M)
    display = output(["xrandr", "--current"])
    modes = re.findall(r"connected(?: primary)?\s+(\d+x\d+)\+", display or "")
    gpu = output(["sh", "-c", "lspci -mm 2>/dev/null | sed -n '/VGA compatible controller/p' | head -1"])
    gpu_name = re.search(r'"([^\"]+)"\s*$', gpu or "")
    if gpu_name and re.fullmatch(r"Device [0-9A-Fa-f]+", gpu_name.group(1)):
        gpu_name = None
    integrated_gpu = re.search(r"Radeon [^,]+", cpu.group(1)) if cpu else None
    version = output(["google-chrome", "--version"])
    cdp = None
    try:
        import urllib.request
        cdp = json.load(urllib.request.urlopen("http://127.0.0.1:9333/json/version", timeout=3))
    except (OSError, ValueError):
        pass
    return {
        "alias": "rack-workstation",
        "reachability": "local browser process",
        "os": platform.system(),
        "architecture": platform.machine(),
        "cpu_model": cpu.group(1) if cpu else None,
        "logical_cpu_count": int(logical.group(1)) if logical else None,
        "memory_total_bytes": int(total.group(1)) * 1024 if total else None,
        "connected_display_modes_px": modes,
        "gpu_class": gpu_name.group(1) if gpu_name else (f"AMD {integrated_gpu.group(0)} (CPU model string)" if integrated_gpu else "NO_DATA (PCI reports only a generic device code)"),
        "browser_version": cdp.get("Browser") if cdp else version,
        "source_commands": ["lscpu", "cat /proc/meminfo", "xrandr --current", "lspci -mm", "google-chrome --version"],
    }


def network_counts():
    raw = output(["tailscale", "status", "--json"])
    if not raw:
        return {"peer_presence": "NO_DATA (Tailscale status unavailable)", "peer_instrumentation": "NO_DATA (no result source)"}
    try:
        state = json.loads(raw)
        peers = state.get("Peer", {}).values()
        count = sum(bool(peer.get("Online")) for peer in peers)
        return {
            "online_network_peer_count": count,
            "peer_measurement_state": "NO_DATA (online presence does not expose a browser/CDP frame sampler)",
            "peer_names_and_addresses": "OMITTED (SCRUB)",
        }
    except (ValueError, AttributeError):
        return {"peer_presence": "NO_DATA (Tailscale status could not be parsed)", "peer_instrumentation": "NO_DATA (no result source)"}


def main():
    receipt = {
        "observed_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "android": android_profile(),
        "rack": rack_profile(),
        "network_census": network_counts(),
    }
    target = Path(__file__).with_name("evidence") / "environment.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(receipt, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"receipt": target.name, "android_online": receipt["android"]["adb_online_device_count"], "network_online": receipt["network_census"].get("online_network_peer_count")}, sort_keys=True))


if __name__ == "__main__":
    main()
