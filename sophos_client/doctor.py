import shutil
import socket
from pathlib import Path
from urllib.parse import urlparse

from sophos_client.config import load_config
from sophos_client.network import current_ssid, portal_reachable


def _resolve_log_path(log_file):
    path = Path(log_file).expanduser()
    if not path.is_absolute():
        project_root = Path(__file__).resolve().parent.parent
        path = project_root / path
    return path


def run_doctor(config_path=None):
    ok = True

    print("[Doctor] Running Sophos WiFi client preflight checks...")

    try:
        cfg = load_config(config_path)
        print("[OK] Config loaded successfully")
    except Exception as exc:
        print(f"[FAIL] Config error: {exc}")
        return False

    iwgetid_path = shutil.which("iwgetid")
    if iwgetid_path:
        print(f"[OK] iwgetid found at: {iwgetid_path}")
    else:
        print("[FAIL] iwgetid not found. Install wireless tools package.")
        ok = False

    interface = cfg.get("ssid_interface") or None
    ssid = current_ssid(interface)
    if ssid:
        print(f"[OK] Current SSID: {ssid}")
    else:
        print("[WARN] Could not read current SSID (not connected or interface mismatch)")

    parsed = urlparse(cfg["portal_url"])
    host = parsed.hostname
    if host:
        try:
            resolved_ip = socket.gethostbyname(host)
            print(f"[OK] Portal host DNS resolution: {host} -> {resolved_ip}")
        except OSError as exc:
            print(f"[FAIL] Portal host DNS resolution failed: {exc}")
            ok = False

    reachable = portal_reachable(cfg["portal_url"], timeout_seconds=cfg["network_probe_timeout"])
    if reachable:
        print("[OK] Portal host is reachable")
    else:
        print("[FAIL] Portal host is not reachable")
        ok = False

    log_path = _resolve_log_path(cfg["log_file"])
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("a", encoding="utf-8"):
            pass
        print(f"[OK] Log path writable: {log_path}")
    except OSError as exc:
        print(f"[FAIL] Log path not writable: {exc}")
        ok = False

    if ok:
        print("[Doctor] All critical checks passed")
    else:
        print("[Doctor] One or more critical checks failed")

    return ok
