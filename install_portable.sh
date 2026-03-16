#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${1:-/opt/sophos-wifi-client}"
CONFIG_DIR="/etc/sophos-wifi-client"
SERVICE_NAME="sophos-wifi-client"
SERVICE_USER="sophoswifi"

echo "Installing Sophos WiFi Client to ${INSTALL_DIR}"

if ! id -u "${SERVICE_USER}" >/dev/null 2>&1; then
  sudo useradd --system --create-home --home-dir /var/lib/sophos-wifi-client --shell /usr/sbin/nologin "${SERVICE_USER}"
fi

sudo mkdir -p "${INSTALL_DIR}" "${CONFIG_DIR}"
sudo cp -r . "${INSTALL_DIR}/"
sudo mkdir -p "${INSTALL_DIR}/logs"
sudo chown -R "${SERVICE_USER}:${SERVICE_USER}" "${INSTALL_DIR}"
sudo chmod -R u=rwX,g=rX,o= "${INSTALL_DIR}"

sudo python3 -m pip install -r "${INSTALL_DIR}/requirements.txt"

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

sudo cp "${INSTALL_DIR}/sophos-wifi-client.service" "/etc/systemd/system/${SERVICE_NAME}.service"
sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}"

echo "Install complete."
echo "Edit ${CONFIG_DIR}/config.yaml (and /etc/default/${SERVICE_NAME}) then run:"
echo "  sudo systemctl start ${SERVICE_NAME}"
