#!/usr/bin/env bash
set -euo pipefail

SERVICE_NAME="${1:-sophos-wifi-client}"
APP_LOG_FILE="${2:-/var/log/sophos-wifi-client/sophos_wifi.log}"
export SERVICE_NAME

echo "[BOOT]"
who -b || true
BOOT_RAW="$(uptime -s)"
echo "Boot timestamp: ${BOOT_RAW}"

echo
echo "[SERVICE]"
systemctl show "${SERVICE_NAME}" -p ActiveState -p ActiveEnterTimestamp --no-pager

echo
echo "[BOOT -> SERVICE ACTIVE DIFF]"
python3 - <<'PY'
from datetime import datetime
import os
import subprocess

service_name = os.environ.get("SERVICE_NAME", "sophos-wifi-client")

boot_raw = subprocess.check_output(["uptime", "-s"], text=True).strip()
svc_raw = subprocess.check_output(
    ["systemctl", "show", service_name, "-p", "ActiveEnterTimestamp", "--value"],
    text=True,
).strip()

if not svc_raw:
    print("Service has no ActiveEnterTimestamp yet")
    raise SystemExit(0)

svc_no_tz = " ".join(svc_raw.split()[:-1])
svc_dt = datetime.strptime(svc_no_tz, "%a %Y-%m-%d %H:%M:%S")
boot_dt = datetime.strptime(boot_raw, "%Y-%m-%d %H:%M:%S")
delta = svc_dt - boot_dt

print(f"boot={boot_dt}")
print(f"service_active={svc_dt}")
print(f"diff_seconds={int(delta.total_seconds())}")
print(f"diff={delta}")
PY

echo
echo "[SERVICE ERRORS/WARNINGS - CURRENT BOOT]"
journalctl -u "${SERVICE_NAME}" -b --no-pager | grep -Ei 'error|failed|warning|traceback|exception' || true

echo
echo "[HEALTHCHECK ERRORS/WARNINGS - CURRENT BOOT]"
journalctl -u "${SERVICE_NAME}-healthcheck.service" -b --no-pager | grep -Ei 'error|failed|alert|warning' || true

echo
echo "[APP LOG ERRORS/WARNINGS]"
if [[ -f "${APP_LOG_FILE}" ]]; then
  grep -Ei 'error|failed|warning|traceback|exception' "${APP_LOG_FILE}" || true
else
  echo "Log file not found: ${APP_LOG_FILE}"
fi
