#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="${1:-/opt/sophos-wifi-client}"
CONFIG_DIR="/etc/sophos-wifi-client"
LOG_DIR="/var/log/sophos-wifi-client"
SERVICE_NAME="sophos-wifi-client"
HEALTHCHECK_SERVICE_NAME="${SERVICE_NAME}-healthcheck"
HEALTHCHECK_TIMER_NAME="${HEALTHCHECK_SERVICE_NAME}.timer"
SERVICE_USER="sophoswifi"

echo "Installing Sophos WiFi Client to ${INSTALL_DIR}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "[ERROR] python3 not found. Install with: sudo apt-get install -y python3"
  exit 1
fi

if ! python3 -m venv --help >/dev/null 2>&1; then
  echo "[ERROR] python3 venv module not available. Install with: sudo apt-get install -y python3-venv"
  exit 1
fi

if ! command -v iwgetid >/dev/null 2>&1; then
  echo "[ERROR] iwgetid not found. Install with: sudo apt-get install -y wireless-tools"
  exit 1
fi

if ! id -u "${SERVICE_USER}" >/dev/null 2>&1; then
  sudo useradd --system --create-home --home-dir /var/lib/sophos-wifi-client --shell /usr/sbin/nologin "${SERVICE_USER}"
fi

sudo mkdir -p "${INSTALL_DIR}" "${CONFIG_DIR}"
sudo cp -r "${SCRIPT_DIR}/." "${INSTALL_DIR}/"
sudo rm -rf "${INSTALL_DIR}/.git"
sudo mkdir -p "${LOG_DIR}"
sudo chown -R "${SERVICE_USER}:${SERVICE_USER}" "${INSTALL_DIR}"
sudo chmod -R u=rwX,g=rX,o= "${INSTALL_DIR}"
sudo chmod 750 "${INSTALL_DIR}/healthcheck.sh"
sudo chown "${SERVICE_USER}:${SERVICE_USER}" "${LOG_DIR}"
sudo chmod 750 "${LOG_DIR}"

sudo -u "${SERVICE_USER}" python3 -m venv "${INSTALL_DIR}/.venv"
sudo -u "${SERVICE_USER}" "${INSTALL_DIR}/.venv/bin/pip" install --upgrade pip
sudo -u "${SERVICE_USER}" "${INSTALL_DIR}/.venv/bin/pip" install -r "${INSTALL_DIR}/requirements.txt"

if [[ ! -f "${CONFIG_DIR}/config.yaml" ]]; then
  sudo cp "${INSTALL_DIR}/config/config.example.yaml" "${CONFIG_DIR}/config.yaml"
fi
sudo chown root:"${SERVICE_USER}" "${CONFIG_DIR}"
sudo chown root:"${SERVICE_USER}" "${CONFIG_DIR}/config.yaml"
sudo chmod 640 "${CONFIG_DIR}/config.yaml"
sudo chmod 750 "${CONFIG_DIR}"

if [[ ! -f "/etc/default/${SERVICE_NAME}" ]]; then
  sudo cp "${INSTALL_DIR}/config/sophos-wifi-client.env.example" "/etc/default/${SERVICE_NAME}"
fi
sudo chown root:"${SERVICE_USER}" "/etc/default/${SERVICE_NAME}"
sudo chmod 640 "/etc/default/${SERVICE_NAME}"

sudo tee "/etc/systemd/system/${SERVICE_NAME}.service" >/dev/null <<EOF
[Unit]
Description=Sophos WiFi Client
Wants=network.target
After=network.target
StartLimitIntervalSec=120
StartLimitBurst=10

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=${INSTALL_DIR}
ExecStart=${INSTALL_DIR}/.venv/bin/python ${INSTALL_DIR}/cli.py --config ${CONFIG_DIR}/config.yaml
Restart=always
RestartSec=5
KillSignal=SIGTERM
TimeoutStopSec=15
TimeoutStartSec=30
UMask=0027
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectHome=true
ProtectSystem=strict
ProtectControlGroups=true
ProtectKernelTunables=true
ProtectKernelModules=true
LockPersonality=true
MemoryDenyWriteExecute=true
RestrictSUIDSGID=true
RestrictRealtime=true
RestrictNamespaces=true
SystemCallArchitectures=native
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
ReadWritePaths=${LOG_DIR}
Environment=PYTHONUNBUFFERED=1
EnvironmentFile=-/etc/default/${SERVICE_NAME}

[Install]
WantedBy=multi-user.target
EOF

sudo tee "/etc/systemd/system/${HEALTHCHECK_SERVICE_NAME}.service" >/dev/null <<EOF
[Unit]
Description=Healthcheck for ${SERVICE_NAME}
After=network.target

[Service]
Type=oneshot
EnvironmentFile=-/etc/default/${SERVICE_NAME}
ExecStart=${INSTALL_DIR}/healthcheck.sh ${SERVICE_NAME}
NoNewPrivileges=true
PrivateTmp=true
PrivateDevices=true
ProtectHome=true
ProtectSystem=strict
ProtectControlGroups=true
ProtectKernelTunables=true
ProtectKernelModules=true
LockPersonality=true
MemoryDenyWriteExecute=true
RestrictSUIDSGID=true
RestrictRealtime=true
RestrictNamespaces=true
SystemCallArchitectures=native
RestrictAddressFamilies=AF_UNIX AF_INET AF_INET6
ReadWritePaths=${LOG_DIR}
EOF

sudo tee "/etc/systemd/system/${HEALTHCHECK_TIMER_NAME}" >/dev/null <<EOF
[Unit]
Description=Periodic healthcheck timer for ${SERVICE_NAME}

[Timer]
OnBootSec=3min
OnUnitActiveSec=10min
RandomizedDelaySec=30s
Persistent=true
Unit=${HEALTHCHECK_SERVICE_NAME}.service

[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"
sudo systemctl enable "${HEALTHCHECK_TIMER_NAME}"

echo "Install complete."
echo "Edit ${CONFIG_DIR}/config.yaml (and /etc/default/${SERVICE_NAME}) then run:"
echo "  sudo systemctl start ${SERVICE_NAME}"
echo "Optional health monitor control:"
echo "  sudo systemctl start ${HEALTHCHECK_TIMER_NAME}"
