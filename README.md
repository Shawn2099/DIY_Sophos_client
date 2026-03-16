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
- `SOPHOSDIY_LOG_LEVEL`
- `SOPHOSDIY_LOG_FILE`
- `SOPHOSDIY_NETWORK_PROBE_ENABLED`

## Verify Deployment Stability

```bash
sudo systemctl status sophos-wifi-client --no-pager
sudo journalctl -u sophos-wifi-client -n 100 --no-pager
```

## Notes

- Use `python3 cli.py --doctor` after any config change.
- Keep secrets in `/etc/default/sophos-wifi-client` for production deployments.
- Keep `config.yaml` non-secret and store real credentials in env file overrides.
