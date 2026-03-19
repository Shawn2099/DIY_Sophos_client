# Sophos WiFi Client

Lightweight Python client for Sophos captive portals (`login.xml` / `logout.xml`) that keeps a user authenticated on a target WiFi SSID.

## Features

- Sophos-compatible login/logout flow (mode `191` and `193`)
- XML response parsing (`LIVE` / `LOGIN`) for robust state handling
- SSID-aware loop with optional interface selection
- Portal reachability probe before auth calls
- Exponential backoff on failures
- Rotating logs
- Graceful exit on `SIGINT` / `SIGTERM`
- Environment variable overrides for secrets and deployment tuning

## Quick Start

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Create config:

```bash
cp config/config.example.yaml config/config.yaml
```

3. Set credentials in either:
- `config/config.yaml`, or
- environment variables (recommended):
  - `SOPHOSDIY_USERNAME`
  - `SOPHOSDIY_PASSWORD`

4. Run:

```bash
python3 cli.py
```

Preflight checks before running:

```bash
python3 cli.py --doctor
```

Optional custom config path:

```bash
python3 cli.py --config /path/to/config.yaml
```

## Systemd (Portable)

Use the portable installer:

```bash
chmod +x install_portable.sh
./install_portable.sh
```

This installs under `/opt/sophos-wifi-client` (or custom path argument), creates:
- `/etc/sophos-wifi-client/config.yaml`
- `/etc/default/sophos-wifi-client`
- `sophos-wifi-client.service`
- `sophos-wifi-client-healthcheck.service`
- `sophos-wifi-client-healthcheck.timer`

By default, the service is hardened to:
- run as dedicated non-root user `sophoswifi`
- restart automatically on failure
- enforce restart throttling to avoid crash loops
- use systemd sandboxing and write access only to `/var/log/sophos-wifi-client`

Default Linux paths used by the installer/service:
- code: `/opt/sophos-wifi-client`
- config: `/etc/sophos-wifi-client/config.yaml`
- env/secrets: `/etc/default/sophos-wifi-client`
- logs: `/var/log/sophos-wifi-client/sophos_wifi.log`

Then start service:

```bash
sudo systemctl start sophos-wifi-client
sudo systemctl status sophos-wifi-client
```

Optional: start periodic health monitoring immediately (otherwise it starts next boot):

```bash
sudo systemctl start sophos-wifi-client-healthcheck.timer
sudo systemctl status sophos-wifi-client-healthcheck.timer --no-pager
```

To uninstall:

```bash
chmod +x uninstall_portable.sh
./uninstall_portable.sh
```

To also remove `/etc/sophos-wifi-client` config directory:

```bash
PURGE_CONFIG=true ./uninstall_portable.sh
```

## Important Environment Overrides

- `SOPHOSDIY_SSID`
- `SOPHOSDIY_PORTAL_URL`
- `SOPHOSDIY_USERNAME`
- `SOPHOSDIY_PASSWORD`
- `SOPHOSDIY_SSID_INTERFACE`
- `SOPHOSDIY_STARTUP_FAST_RETRY_SECONDS`
- `SOPHOSDIY_LOG_LEVEL`
- `SOPHOSDIY_LOG_FILE`
- `SOPHOSDIY_NETWORK_PROBE_ENABLED`

## Verify Deployment Stability

```bash
sudo systemctl status sophos-wifi-client --no-pager
sudo journalctl -u sophos-wifi-client -n 100 --no-pager
sudo systemctl list-timers | grep sophos-wifi-client-healthcheck
sudo journalctl -u sophos-wifi-client-healthcheck.service -n 50 --no-pager
```

Quick error scan (service + healthcheck + app log):

```bash
sudo sh -lc 'journalctl -u sophos-wifi-client -b --no-pager | grep -Ei "error|failed|warning|traceback|exception" || true; journalctl -u sophos-wifi-client-healthcheck.service -b --no-pager | grep -Ei "error|failed|alert|warning" || true; grep -Ei "error|failed|warning|traceback|exception" /var/log/sophos-wifi-client/sophos_wifi.log || true'
```

Reusable runtime diagnostics script (includes boot-to-service-start time diff + error scans):

```bash
chmod +x scripts/check_runtime.sh
sudo ./scripts/check_runtime.sh
```

Optional custom service or log path:

```bash
sudo ./scripts/check_runtime.sh sophos-wifi-client /var/log/sophos-wifi-client/sophos_wifi.log
```

## Notes

- Use `python3 cli.py --doctor` after any config change.
- Keep secrets in `/etc/default/sophos-wifi-client` for production deployments.
- Keep `config.yaml` non-secret and store real credentials in env file overrides.
